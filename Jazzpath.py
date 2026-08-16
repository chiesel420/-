import streamlit as st
import requests
import random
from urllib.parse import quote

# ====================== 配置 ======================
DISCOGS_TOKEN = "FzgZDYmHewczBWNAleqNOtsgAckQraBebyLClate"   # ← 请替换成你的真实 Token
# =================================================

st.set_page_config(
    page_title="Jazz Path",
    page_icon="🎷",
    layout="centered"
)

# 深色简洁风格
st.markdown("""
    <style>
    .stApp {
        background-color: #171717;
        color: #ffffff;
    }
    .song-card {
        background-color: #2a2a2a;
        padding: 20px;
        border-radius: 16px;
        margin-bottom: 20px;
    }
    .song-title {
        font-size: 20px;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 6px;
    }
    .song-artist {
        font-size: 15px;
        color: #aaaaaa;
        margin-bottom: 6px;
    }
    .song-meta {
        font-size: 14px;
        color: #cccccc;
        margin-bottom: 12px;
    }
    a.button-link {
        display: inline-block;
        background-color: #3a3a3a;
        color: #ffffff !important;
        padding: 6px 12px;
        border-radius: 8px;
        text-decoration: none;
        font-size: 13px;
        margin-right: 8px;
    }
    a.button-link:hover {
        background-color: #4a4a4a;
    }
    .axis-label {
        font-size: 14px;
        color: #aaaaaa;
        margin-bottom: 4px;
    }
    </style>
""", unsafe_allow_html=True)

# ====================== 二维情绪映射表 ======================
# X轴: Relaxed (低) ←→ Energetic (高)
# Y轴: Refined (低) ←→ Complex (高)
style_emotion_map = {
    "Cool Jazz":    {"x": 2, "y": 3},   # 很Relaxed + 较Refined
    "Hard Bop":     {"x": 8, "y": 5},   # 较Energetic + 中等
    "Bebop":        {"x": 7, "y": 9},   # Energetic + 很Complex
    "Modal Jazz":   {"x": 3, "y": 7},   # 较Relaxed + 较Complex
    "Free Jazz":    {"x": 6, "y": 10},  # 中等偏Energetic + 极Complex
    "Soul Jazz":    {"x": 7, "y": 3},   # Energetic + Refined
    "Jazz-Funk":    {"x": 9, "y": 4},   # 很Energetic + 较Refined
    "Post Bop":     {"x": 6, "y": 7},   # 中等 + 较Complex
    "Swing":        {"x": 4, "y": 2},   # 较Relaxed + 很Refined
    "Latin Jazz":   {"x": 8, "y": 4},   # Energetic + 较Refined
}

def find_best_styles(user_x, user_y, top_n=3):
    """根据用户在二维坐标系的位置，返回最接近的几个风格"""
    distances = []
    
    for style, pos in style_emotion_map.items():
        # 计算欧几里得距离
        distance = ((pos["x"] - user_x) ** 2 + (pos["y"] - user_y) ** 2) ** 0.5
        distances.append((style, distance))
    
    # 按距离排序，取前 top_n 个
    distances.sort(key=lambda x: x[1])
    top_styles = [item[0] for item in distances[:top_n]]
    
    # 从最接近的几个风格中随机选一个
    return random.choice(top_styles)

def get_jazz_songs(style):
    encoded_style = quote(style)
    
    # 按收藏数排序，优先返回质量较高的结果
    url = f"https://api.discogs.com/database/search?type=release&style={encoded_style}&per_page=8&sort=have&sort_order=desc"
    
    headers = {
        "User-Agent": "JazzPath/1.0",
        "Authorization": f"Discogs token={DISCOGS_TOKEN}"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        results = data.get("results", [])
        
        # 随机抽取4首，增加变化
        if len(results) >= 4:
            results = random.sample(results, 4)
        else:
            results = results[:4]
        
        songs = []
        for result in results:
            full_title = result.get("title", "Unknown")
            
            if " - " in full_title:
                parts = full_title.split(" - ", 1)
                artist = parts[0]
                title = parts[1]
            else:
                artist = "Unknown Artist"
                title = full_title
            
            country = result.get("country", "Unknown")
            
            songs.append({
                "title": title,
                "artist": artist,
                "meta": country
            })
        return songs, None
    except Exception as e:
        return [], str(e)

# ====================== 页面内容 ======================
st.title("Jazz Path")
st.caption("Move on the mood map to find your Jazz")

# ===== 二维坐标系滑条 =====
st.markdown("**Horizontal Axis: Relaxed ←→ Energetic**")
x_value = st.slider("Relaxed  ←→  Energetic", 1, 10, 5, label_visibility="collapsed")

st.markdown("**Vertical Axis: Refined ←→ Complex**")
y_value = st.slider("Refined  ←→  Complex", 1, 10, 5, label_visibility="collapsed")

st.write("")  # 空行分隔

# 推荐按钮
if st.button("🔄 Get Recommendations", use_container_width=True):
    best_style = find_best_styles(x_value, y_value)
    
    with st.spinner("Finding matching Jazz..."):
        songs, error = get_jazz_songs(best_style)
    
    if error:
        st.error(f"加载失败: {error}")
    elif not songs:
        st.warning("没有获取到歌曲，请检查 Token 或网络。")
    else:
        for song in songs:
            query = quote(f"{song['artist']} {song['title']}")
            apple_url = f"https://music.apple.com/search?term={query}"
            spotify_url = f"https://open.spotify.com/search/{query}"
            youtube_url = f"https://music.youtube.com/search?q={query}"
            
            st.markdown(f"""
            <div class="song-card">
                <div class="song-title">{song['title']}</div>
                <div class="song-artist">{song['artist']}</div>
                <div class="song-meta">{song['meta']}</div>
                <a href="{apple_url}" target="_blank" class="button-link">Apple Music</a>
                <a href="{spotify_url}" target="_blank" class="button-link">Spotify</a>
                <a href="{youtube_url}" target="_blank" class="button-link">YouTube</a>
            </div>
            """, unsafe_allow_html=True) 
