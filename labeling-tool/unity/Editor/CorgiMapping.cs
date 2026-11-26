// Corgi Engine 매핑: 엔진 컴포넌트·충돌 레이어 → 라벨링 클래스 (labeling-tool/labeling_guide_v0.md 기준)
// 규칙 표와 한계는 labeling-tool/README.md
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using MoreMountains.CorgiEngine;
using MoreMountains.InventoryEngine;
using MoreMountains.Tools;
using UnityEditor;
using UnityEngine;
using UnityEngine.UI;

namespace GameQa.Extract
{
    public class CorgiMapping : IMapping
    {
        const BindingFlags Hidden = BindingFlags.Instance | BindingFlags.NonPublic;
        static readonly FieldInfo ReticleField = typeof(WeaponAim).GetField("_reticle", Hidden);
        static readonly FieldInfo ProgressBarField = typeof(MMHealthBar).GetField("_progressBar", Hidden);

        readonly int solid, oneWay, stairs;
        readonly HashSet<GameObject> reticles;
        readonly IReadOnlyList<string[]> hudGroups;

        public Camera WorldCamera { get; }
        public Camera ScreenCamera { get; }

        /// <param name="reference">충돌 기준 컨트롤러 (플레이어)</param>
        /// <param name="hudGroups">기능 컴포넌트가 없는 HUD 기능 단위 (GameObject 이름 묶음, 가이드 5장 8)</param>
        public CorgiMapping(Camera world, Camera screen, CorgiController reference, IReadOnlyList<string[]> hudGroups)
        {
            WorldCamera = world;
            ScreenCamera = screen;
            this.hudGroups = hudGroups;
            // 가이드 4장: Terrain은 캐릭터가 부딪히는 것, Platform은 아래에서 통과 가능한 것. 계단은 Terrain
            solid = reference.PlatformMask;
            oneWay = reference.OneWayPlatformMask | reference.MovingOneWayPlatformMask | reference.MidHeightOneWayPlatformMask;
            stairs = reference.StairsMask;
            // 가이드 5장 7: 조준 표시는 v0에서 칠하지 않음
            reticles = new HashSet<GameObject>(Object.FindObjectsByType<WeaponAim>(FindObjectsSortMode.None)
                .Select(a => ReticleField.GetValue(a) as GameObject).Where(r => r != null));
        }

        public Instance? Classify(Renderer r)
        {
            // 가이드 1장: 이펙트·파티클은 칠하지 않음. 4장: 줄은 칠하지 않음
            if (r is ParticleSystemRenderer || r is TrailRenderer || r is LineRenderer) return null;
            if (reticles.Contains(r.gameObject)) return null;
            // 무기는 캐릭터 아래에 붙으므로 캐릭터보다 먼저
            var weapon = r.GetComponentInParent<Weapon>();
            if (weapon != null) return new Instance("Equipment", weapon);
            var character = r.GetComponentInParent<Character>();
            if (character != null) return new Instance("Character", character);
            Component item = r.GetComponentInParent<PickableItem>();
            if (item == null) item = r.GetComponentInParent<ItemPicker>();
            if (item != null) return new Instance("LooseObject", item);
            var collider = r.GetComponent<Collider2D>();
            int bit = 1 << r.gameObject.layer;
            if (collider != null && !collider.isTrigger && (solid & bit) != 0)
                return new Instance((oneWay & bit) != 0 && (stairs & bit) == 0 ? "Platform" : "Terrain", r);
            return null;
        }

        IEnumerable<(MMHealthBar, MMProgressBar)> HealthBars() =>
            Object.FindObjectsByType<MMHealthBar>(FindObjectsSortMode.None)
                .Select(h => (h, ProgressBarField.GetValue(h) as MMProgressBar)).Where(p => p.Item2 != null);

        public IEnumerable<Unit> WorldUnits() =>
            HealthBars().Select(p => new Unit(new Instance("HealthBar", p.Item1), p.Item2.GetComponentsInChildren<Graphic>()));

        public IEnumerable<Unit> ScreenUnits(IReadOnlyList<Graphic> visible)
        {
            // 가이드 5장 8: HUD는 기능 하나 = 인스턴스 하나. 기능 컴포넌트 단위, 없으면 hudGroups
            var roots = new Dictionary<Object, List<Graphic>>();
            foreach (var g in visible)
            {
                Component root = g.GetComponentInParent<MMProgressBar>();
                if (root == null) root = g.GetComponentInParent<InventoryDisplay>();
                Object key = root;
                if (key == null)
                {
                    var group = hudGroups.FirstOrDefault(names => names.Contains(g.name));
                    if (group != null) key = visible.First(v => v.name == group[0]);
                }
                if (key == null) continue;
                if (!roots.TryGetValue(key, out var list)) roots[key] = list = new List<Graphic>();
                list.Add(g);
            }
            foreach (var kv in roots) yield return new Unit(new Instance("HUDElement", kv.Key), kv.Value);
            // 가이드 5장 10: 글자 덩어리 하나 = 인스턴스 하나 (Text 컴포넌트 단위)
            foreach (var g in visible)
                if (g is Text) yield return new Unit(new Instance("TextLabel", g), new[] { g });
        }

        public IEnumerable<Relation> Relations()
        {
            // 가이드 6장: attachedTo Equipment → Character, represents HealthBar → 대상
            foreach (var w in Object.FindObjectsByType<Weapon>(FindObjectsSortMode.None))
                if (w.Owner != null) yield return new Relation("attachedTo", new Instance("Equipment", w), new Instance("Character", w.Owner));
            foreach (var (h, _) in HealthBars())
            {
                var target = h.GetComponent<Character>();
                if (target != null) yield return new Relation("represents", new Instance("HealthBar", h), new Instance("Character", target));
            }
        }
    }

    public static class CorgiCapture
    {
        // Retro 데모 HUD: 아바타 머리·배경이 기능 하나 (기능 컴포넌트 없음)
        static readonly string[][] RetroHudGroups = { new[] { "AvatarHead", "AvatarBackground" } };

        /// <summary>플레이 모드에서 현재 프레임 추출. 반환: 요약</summary>
        public static string Run(string outDir)
        {
            if (!EditorApplication.isPlaying) throw new System.InvalidOperationException("플레이 모드에서 실행");
            var player = LevelManager.Instance.Players[0].GetComponent<CorgiController>();
            var screen = Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None)
                .FirstOrDefault(c => c.isRootCanvas && c.renderMode == RenderMode.ScreenSpaceCamera)?.worldCamera;
            return Capture.Run(new CorgiMapping(Camera.main, screen, player, RetroHudGroups), outDir);
        }

        [MenuItem("GameQA/현재 프레임 추출")]
        static void Menu()
        {
            var dir = Path.Combine(Path.GetDirectoryName(Application.dataPath), "GameQaCapture", System.DateTime.Now.ToString("yyyyMMdd_HHmmss"));
            Debug.Log($"GameQA: {Run(dir)} → {dir}");
        }
    }
}
