// 인스턴스 ID 색 렌더: 텍스처 알파(× 정점 알파) 0.5 미만은 버리고 나머지는 _IdColor 단색. 혼합 없음
Shader "Hidden/GameQa/Id"
{
    Properties
    {
        _MainTex ("Texture", 2D) = "white" {}
        _IdColor ("Id", Color) = (0, 0, 0, 1)
    }
    SubShader
    {
        Tags { "Queue" = "Transparent" }
        Cull Off
        ZWrite Off
        Blend Off
        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"

            sampler2D _MainTex;
            fixed4 _IdColor;

            struct appdata { float4 vertex : POSITION; float2 uv : TEXCOORD0; fixed4 color : COLOR; };
            struct v2f { float4 pos : SV_POSITION; float2 uv : TEXCOORD0; fixed4 color : COLOR; };

            v2f vert(appdata v)
            {
                v2f o;
                o.pos = UnityObjectToClipPos(v.vertex);
                o.uv = v.uv;
                o.color = v.color;
                return o;
            }

            fixed4 frag(v2f i) : SV_Target
            {
                clip(tex2D(_MainTex, i.uv).a * i.color.a - 0.5);
                return _IdColor;
            }
            ENDCG
        }
    }
}
