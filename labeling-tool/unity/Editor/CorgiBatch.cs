// Corgi 일괄 추출: 플레이 모드 한 번으로 장면 목록을 차례로 불러와 장면마다 플레이어를 여러 위치에 배치한 뒤 추출
// 정상 화면만 만들도록 착지·생존·지형 비겹침일 때만 추출. 결과 요약은 <출력 루트>/batch.json
using System.Collections.Generic;
using System.IO;
using MoreMountains.CorgiEngine;
using MoreMountains.Tools;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace GameQa.Extract
{
    public static class CorgiBatch
    {
        const int LoadWaitFrames = 60;
        const int SettleFrames = 45;
        const int AttemptsPerFrame = 10;

        [System.Serializable] class Entry { public string scene, folder, result; public float x, y; }
        [System.Serializable] class Summary { public List<Entry> frames = new List<Entry>(); public string status; }

        static IEnumerator<object> job;
        static Summary summary;
        static string root;

        /// <summary>진행 상황 (MCP 등에서 확인)</summary>
        public static string Status { get; private set; } = "idle";

        /// <param name="scenes">장면 에셋 경로</param>
        /// <param name="framesPerScene">장면마다 추출할 프레임 수</param>
        /// <param name="attachHealthBars">체력바 없는 적에 MMHealthBar를 실행 중 부착 (씬 파일은 그대로)</param>
        public static void Start(string[] scenes, string outRoot, int framesPerScene, int seed = 0, bool attachHealthBars = true, string game = "corgi")
        {
            if (!EditorApplication.isPlaying) throw new System.InvalidOperationException("플레이 모드에서 실행");
            if (job != null) throw new System.InvalidOperationException("실행 중: " + Status);
            root = outRoot;
            Directory.CreateDirectory(root);
            summary = new Summary();
            job = Run(scenes, framesPerScene, seed, attachHealthBars, game).GetEnumerator();
            EditorApplication.update += Step;
            Status = "started";
        }

        public static void Stop() => Finish("stopped");

        static void Step()
        {
            if (!EditorApplication.isPlaying) { Finish("stopped: 플레이 모드 종료"); return; }
            try
            {
                if (!job.MoveNext()) Finish($"done: {summary.frames.FindAll(f => f.result.StartsWith("ok")).Count} frames");
            }
            catch (System.Exception e)
            {
                Finish("error: " + e.Message);
                Debug.LogException(e);
            }
        }

        static void Finish(string status)
        {
            EditorApplication.update -= Step;
            job = null;
            Status = status;
            if (summary != null)
            {
                summary.status = status;
                File.WriteAllText(Path.Combine(root, "batch.json"), JsonUtility.ToJson(summary, true));
            }
        }

        static IEnumerable<object> WaitFrames(int n)
        {
            int until = Time.frameCount + n;
            while (Time.frameCount < until) yield return null;
        }

        static IEnumerable<object> Run(string[] scenes, int framesPerScene, int seed, bool attachHealthBars, string game)
        {
            foreach (var path in scenes)
            {
                var scene = Path.GetFileNameWithoutExtension(path);
                Status = $"{scene}: loading";
                var op = EditorSceneManager.LoadSceneAsyncInPlayMode(path, new LoadSceneParameters(LoadSceneMode.Single));
                while (!op.isDone) yield return null;
                foreach (var w in WaitFrames(LoadWaitFrames)) yield return w;
                var level = LevelManager.Instance;
                if (level == null || level.Players == null || level.Players.Count == 0)
                {
                    summary.frames.Add(new Entry { scene = scene, result = "skipped: 플레이어 없음" });
                    continue;
                }
                var player = level.Players[0];
                var controller = player.GetComponent<CorgiController>();
                foreach (var fps in Object.FindObjectsByType<MMFPSCounter>(FindObjectsSortMode.None)) fps.gameObject.SetActive(false);
                if (attachHealthBars)
                    foreach (var c in Object.FindObjectsByType<Character>(FindObjectsSortMode.None))
                        if (c != player && c.GetComponent<Health>() != null && c.GetComponent<MMHealthBar>() == null) c.gameObject.AddComponent<MMHealthBar>();

                var rng = new System.Random(seed ^ StableHash(scene));
                int captured = 0;
                for (int attempt = 0; captured < framesPerScene && attempt < framesPerScene * AttemptsPerFrame; attempt++)
                {
                    var b = level.LevelBounds;
                    var p = new Vector2(Mathf.Lerp(b.min.x, b.max.x, (float)rng.NextDouble()), Mathf.Lerp(b.min.y, b.max.y, (float)rng.NextDouble()));
                    if (Physics2D.OverlapBox(p + controller.ColliderOffset, controller.ColliderSize, 0f, controller.PlatformMask) != null) continue;
                    Status = $"{scene}: frame {captured} attempt {attempt}";
                    controller.SetTransformPosition(p);
                    controller.AnchorToGround();
                    controller.SetForce(Vector2.zero);
                    foreach (var w in WaitFrames(SettleFrames)) yield return w;

                    var entry = new Entry { scene = scene, x = player.transform.position.x, y = player.transform.position.y };
                    var reason = Invalid(player, controller, b);
                    if (reason != null)
                    {
                        entry.result = "skipped: " + reason;
                        summary.frames.Add(entry);
                        continue;
                    }
                    entry.folder = $"{game}_{scene}_{captured:00}";
                    entry.result = "ok: " + CorgiCapture.Run(Path.Combine(root, entry.folder));
                    summary.frames.Add(entry);
                    captured++;
                }
            }
        }

        /// <summary>정상 화면이 아니면 이유. 착지, 생존, 고체 지형과 비겹침 (일방 발판은 통과 중일 수 있어 제외)</summary>
        static string Invalid(Character player, CorgiController controller, Bounds bounds)
        {
            if (player.ConditionState.CurrentState != CharacterStates.CharacterConditions.Normal) return "상태 " + player.ConditionState.CurrentState;
            if (!controller.State.IsGrounded) return "공중";
            if (!bounds.Contains(new Vector3(player.transform.position.x, player.transform.position.y, bounds.center.z))) return "레벨 경계 밖";
            int solidOnly = controller.PlatformMask & ~(controller.OneWayPlatformMask | controller.MovingOneWayPlatformMask | controller.MidHeightOneWayPlatformMask);
            if (Physics2D.OverlapBox(controller.ColliderCenterPosition, controller.ColliderSize * 0.9f, 0f, solidOnly) != null) return "지형과 겹침";
            return null;
        }

        /// <summary>실행 환경과 무관한 문자열 해시 (FNV-1a)</summary>
        static int StableHash(string s)
        {
            unchecked
            {
                uint h = 2166136261;
                foreach (var ch in s) { h ^= ch; h *= 16777619; }
                return (int)h;
            }
        }
    }
}
