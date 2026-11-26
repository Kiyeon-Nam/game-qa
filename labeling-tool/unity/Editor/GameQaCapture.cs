// 엔진 추출 라벨: 현재 프레임의 원본 화면, 월드 인스턴스 ID 렌더, 화면 UI 단위 마스크, 관계를 한 프레임 안에서 출력
// 게임별 판단(클래스, 인스턴스 단위, 관계)은 IMapping 구현에. 출력 형식은 labeling-tool/README.md
using System.Collections.Generic;
using System.IO;
using UnityEngine;
using UnityEngine.UI;

namespace GameQa.Extract
{
    /// <summary>인스턴스: 라벨링 클래스와 인스턴스를 대표하는 엔진 오브젝트</summary>
    public readonly struct Instance
    {
        public readonly string Class;
        public readonly Object Owner;
        public Instance(string cls, Object owner) { Class = cls; Owner = owner; }
    }

    /// <summary>UI 단위: Graphic 묶음 하나가 인스턴스 하나</summary>
    public readonly struct Unit
    {
        public readonly Instance Instance;
        public readonly IReadOnlyList<Graphic> Graphics;
        public Unit(Instance instance, IReadOnlyList<Graphic> graphics) { Instance = instance; Graphics = graphics; }
    }

    public readonly struct Relation
    {
        public readonly string Type;
        public readonly Instance Subject, Object;
        public Relation(string type, Instance subject, Instance obj) { Type = type; Subject = subject; Object = obj; }
    }

    public interface IMapping
    {
        Camera WorldCamera { get; }
        /// <summary>화면 UI 카메라. 없으면 null</summary>
        Camera ScreenCamera { get; }
        /// <summary>렌더러의 인스턴스. 칠하지 않으면 null (그래도 뒤를 가림)</summary>
        Instance? Classify(Renderer renderer);
        /// <summary>월드 공간 UI 단위 (개체를 따라다니는 체력바 등). 월드 ID 렌더에 포함</summary>
        IEnumerable<Unit> WorldUnits();
        /// <summary>화면 UI 단위. visible: 보이는 화면 UI Graphic</summary>
        IEnumerable<Unit> ScreenUnits(IReadOnlyList<Graphic> visible);
        /// <summary>엔진 참조로 정해지는 관계 (가이드 6장)</summary>
        IEnumerable<Relation> Relations();
    }

    public static class Capture
    {
        const float MinAlpha = 0.05f;

        [System.Serializable] class WorldEntry { public int id; public int[] color; public string @class; public string engine; }
        [System.Serializable] class UiEntry { public int id; public string mask; public string @class; public string engine; }
        [System.Serializable] class RelationEntry { public string type; public int subject; public int @object; }
        [System.Serializable] class Meta
        {
            public string image = "frame.png", world_ids = "ids_world.png", occluder = "ui_occluder.png";
            public int width, height;
            public List<WorldEntry> world = new List<WorldEntry>();
            public List<UiEntry> ui = new List<UiEntry>();
            public List<RelationEntry> relations = new List<RelationEntry>();
        }

        /// <summary>ID → 색. R·G: ID, B: 검사값 (혼합된 픽셀 검출). 0은 배경</summary>
        static Color32 IdColor(int id) =>
            id == 0 ? new Color32(0, 0, 0, 255) : new Color32((byte)(id & 255), (byte)(id >> 8), (byte)(id * 97 % 251 + 1), 255);

        public static string Run(IMapping mapping, string outDir, int width = 1920, int height = 1080)
        {
            Directory.CreateDirectory(outDir);
            var shader = Shader.Find("Hidden/GameQa/Id");
            if (shader == null) throw new System.InvalidOperationException("Hidden/GameQa/Id 셰이더 없음");
            var meta = new Meta { width = width, height = height };
            var rt = new RenderTexture(width, height, 24, RenderTextureFormat.ARGB32) { antiAliasing = 1 };
            var tex = new Texture2D(width, height, TextureFormat.RGB24, false);
            var materials = new List<Material>();
            Material Solid(Color32 c) { var m = new Material(shader); m.SetColor("_IdColor", c); materials.Add(m); return m; }
            void Save(string name)
            {
                RenderTexture.active = rt;
                tex.ReadPixels(new Rect(0, 0, width, height), 0, 0);
                tex.Apply();
                RenderTexture.active = null;
                File.WriteAllBytes(Path.Combine(outDir, name), tex.EncodeToPNG());
            }
            var world = mapping.WorldCamera;
            var screen = mapping.ScreenCamera;
            try
            {
                // 원본 화면
                Render(world, rt);
                if (screen != null) Render(screen, rt);
                Save(meta.image);

                // 인스턴스 id: (클래스, 엔진 오브젝트)마다 하나
                var ids = new Dictionary<(string, int), int>();
                var idMaterials = new Dictionary<int, Material>();
                int IdOf(Instance x, string engine)
                {
                    var key = (x.Class, x.Owner.GetInstanceID());
                    if (!ids.TryGetValue(key, out var id))
                    {
                        id = ids.Count + 1;
                        ids[key] = id;
                        var c = IdColor(id);
                        meta.world.Add(new WorldEntry { id = id, color = new int[] { c.r, c.g, c.b }, @class = x.Class, engine = engine });
                    }
                    return id;
                }
                Material IdMaterial(int id)
                {
                    if (!idMaterials.TryGetValue(id, out var m)) idMaterials[id] = m = Solid(IdColor(id));
                    return m;
                }

                // 월드 ID 렌더: 모든 렌더러를 ID 단색으로 (칠하지 않는 것은 0으로 그려 뒤를 가림)
                var renderers = new List<(Renderer, Material[])>();
                var graphics = new List<(Graphic, Material)>();
                try
                {
                    foreach (var r in Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None))
                    {
                        if (!r.enabled || !r.gameObject.activeInHierarchy) continue;
                        var x = mapping.Classify(r);
                        var m = IdMaterial(x.HasValue ? IdOf(x.Value, PathOf(x.Value.Owner)) : 0);
                        renderers.Add((r, r.sharedMaterials));
                        var swapped = new Material[r.sharedMaterials.Length];
                        for (int i = 0; i < swapped.Length; i++) swapped[i] = m;
                        r.sharedMaterials = swapped;
                    }
                    foreach (var u in mapping.WorldUnits())
                    {
                        var m = IdMaterial(IdOf(u.Instance, PathOf(u.Instance.Owner)));
                        foreach (var g in u.Graphics)
                        {
                            if (!Visible(g)) continue;
                            graphics.Add((g, OwnMaterial(g)));
                            g.material = m;
                        }
                    }
                    Canvas.ForceUpdateCanvases();
                    RenderIds(world, rt);
                    Save(meta.world_ids);
                }
                finally
                {
                    foreach (var (r, ms) in renderers) r.sharedMaterials = ms;
                    foreach (var (g, m) in graphics) g.material = m;
                }

                foreach (var rel in mapping.Relations())
                    meta.relations.Add(new RelationEntry { type = rel.Type, subject = IdOf(rel.Subject, PathOf(rel.Subject.Owner)), @object = IdOf(rel.Object, PathOf(rel.Object.Owner)) });

                // 화면 UI: 단위마다 따로 렌더 (가이드 2-3 겹침), 마지막에 전체를 가림 마스크로
                if (screen != null)
                {
                    var visible = new List<Graphic>();
                    foreach (var g in Object.FindObjectsByType<Graphic>(FindObjectsSortMode.None))
                        if (Visible(g) && g.canvas.rootCanvas.renderMode != RenderMode.WorldSpace) visible.Add(g);
                    var own = new List<(Graphic, Material)>();
                    foreach (var g in visible) own.Add((g, OwnMaterial(g)));
                    var white = Solid(new Color32(255, 255, 255, 255));
                    var black = Solid(new Color32(0, 0, 0, 255));
                    try
                    {
                        int k = 0;
                        foreach (var u in mapping.ScreenUnits(visible))
                        {
                            var inUnit = new HashSet<Graphic>(u.Graphics);
                            foreach (var g in visible) g.material = inUnit.Contains(g) ? white : black;
                            Canvas.ForceUpdateCanvases();
                            RenderIds(screen, rt);
                            var name = $"ui_{k++}.png";
                            Save(name);
                            meta.ui.Add(new UiEntry { id = ids.Count + meta.ui.Count + 1, mask = name, @class = u.Instance.Class, engine = PathOf(u.Instance.Owner) });
                        }
                        foreach (var g in visible) g.material = white;
                        Canvas.ForceUpdateCanvases();
                        RenderIds(screen, rt);
                        Save(meta.occluder);
                    }
                    finally
                    {
                        foreach (var (g, m) in own) g.material = m;
                    }
                }
                File.WriteAllText(Path.Combine(outDir, "meta.json"), JsonUtility.ToJson(meta, true));
                return $"world {meta.world.Count}, ui {meta.ui.Count}, relations {meta.relations.Count}";
            }
            finally
            {
                rt.Release();
                Object.DestroyImmediate(rt);
                Object.DestroyImmediate(tex);
                foreach (var m in materials) Object.DestroyImmediate(m);
            }
        }

        static bool Visible(Graphic g) =>
            g.enabled && g.gameObject.activeInHierarchy && g.color.a >= MinAlpha && g.canvasRenderer.GetInheritedAlpha() >= MinAlpha;

        static Material OwnMaterial(Graphic g) => g.material == g.defaultMaterial ? null : g.material;

        static void Render(Camera cam, RenderTexture rt)
        {
            cam.targetTexture = rt;
            cam.Render();
            cam.targetTexture = null;
        }

        static readonly string[] RenderCallbacks = { "OnRenderImage", "OnPreCull", "OnPreRender", "OnPostRender" };

        /// <summary>렌더 콜백이 있는 카메라 컴포넌트 (후처리·이미지 효과)</summary>
        static bool IsCameraEffect(MonoBehaviour b)
        {
            const System.Reflection.BindingFlags flags = System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.NonPublic;
            foreach (var name in RenderCallbacks)
                for (var t = b.GetType(); t != null && t != typeof(MonoBehaviour); t = t.BaseType)
                    if (t.GetMethod(name, flags | System.Reflection.BindingFlags.DeclaredOnly) != null) return true;
            return false;
        }

        /// <summary>ID 렌더: 검은 배경, 카메라 효과·MSAA·HDR 끔 (색이 섞이거나 바뀌지 않게)</summary>
        static void RenderIds(Camera cam, RenderTexture rt)
        {
            var effects = new List<MonoBehaviour>();
            foreach (var b in cam.GetComponents<MonoBehaviour>()) if (b.enabled && IsCameraEffect(b)) { b.enabled = false; effects.Add(b); }
            var (flags, bg, msaa, hdr) = (cam.clearFlags, cam.backgroundColor, cam.allowMSAA, cam.allowHDR);
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.backgroundColor = Color.black;
            cam.allowMSAA = false;
            cam.allowHDR = false;
            try { Render(cam, rt); }
            finally
            {
                (cam.clearFlags, cam.backgroundColor, cam.allowMSAA, cam.allowHDR) = (flags, bg, msaa, hdr);
                foreach (var b in effects) b.enabled = true;
            }
        }

        static string PathOf(Object o)
        {
            var t = o is Component c ? c.transform : (o as GameObject)?.transform;
            if (t == null) return o.name;
            var path = t.name;
            for (var p = t.parent; p != null; p = p.parent) path = p.name + "/" + path;
            return path;
        }
    }
}
