import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
import os

# --- 1. THE CRITICAL FONT FIX ---
# We need a font that supports Vietnamese Diacritics. 
# 'Arial' or 'Times New Roman' on Windows are safer for Vietnamese than 'YaHei'.
FONT_PATH = "C:/Windows/Fonts/arial.ttf" 
if not os.path.exists(FONT_PATH):
    # Fallback to any available system font if Arial isn't there
    FONT_PATH = "C:/Windows/Fonts/msgothic.ttc" 

LANG_MAP = {
    'en': 'English', 'vi': 'Vietnamese', 'zh-cn': 'Chinese (Simplified)',
    'ko': 'Korean', 'id': 'Indonesian', 'ms': 'Malay', 'th': 'Thai',
    'tl': 'Tagalog', 'ja': 'Japanese', 'hi': 'Hindi', 'fr': 'French'
}

@st.cache_data
def load_csv(path):
    if os.path.exists(path):
        return pd.read_csv(path)
    return None

st.set_page_config(page_title="TikTok Engagement Dashboard", layout="wide")
st.title("📊 TikTok Engagement Analysis Dashboard")

tab1, tab2, tab3, tab4 = st.tabs([
    "Meme Lifecycle", "Cultural Resonance", "Sentiment Analysis", "Fan Radar"
])

# --- TAB 1: MEME LIFECYCLE (Dropdown/Button Fix) ---
with tab1:
    st.header("Meme Lifecycle: Frequency & Engagement")
    df1 = load_csv('meme_time_series.csv')
    if df1 is not None:
        df1['start_date'] = pd.to_datetime(df1['week'].str.split('/').str[0])
        df1 = df1.sort_values('start_date')
        
        buzzwords = df1['buzzword'].unique()
        fig1 = go.Figure()

        for meme in buzzwords:
            m_data = df1[df1['buzzword'] == meme]
            fig1.add_trace(go.Scatter(
                x=m_data['start_date'], y=m_data['frequency'],
                mode='lines+markers', name=meme, line_shape='spline',
                customdata=m_data[['avg_likes', 'week']],
                hovertemplate="<b>%{text}</b><br>Freq: %{y}<br>Avg Likes: %{customdata[0]:.0f}<extra></extra>",
                text=[meme] * len(m_data)
            ))

        # Improved UI: No white-on-white buttons
        fig1.update_layout(
            template='plotly_dark',
            updatemenus=[
                dict(
                    type="dropdown", direction="down", x=1.1, y=1.1, showactive=True,
                    bgcolor="#2b2b2b", font=dict(color="white"),
                    buttons=[dict(label="Show All", method="update", args=[{"visible": [True]*len(buzzwords)}])] +
                             [dict(label=m, method="update", args=[{"visible": [bw == m for bw in buzzwords]}]) for m in buzzwords]
                ),
                dict(
                    type="buttons", direction="left", x=0, y=1.1, showactive=True,
                    bgcolor="#2b2b2b", font=dict(color="white"),
                    buttons=[dict(label="Linear", method="relayout", args=[{"yaxis.type": "linear"}]),
                              dict(label="Log Scale", method="relayout", args=[{"yaxis.type": "log"}])]
                )
            ]
        )
        st.plotly_chart(fig1, width='stretch')

# --- TAB 2: TREEMAP (Language Color Fix) ---
with tab2:
    st.header("Cross-Cultural Resonance")
    df2 = load_csv('stage1_language_engagement.csv')
    if df2 is not None:
        df2 = df2[df2['Total_Comments'] > 0].copy()
        df2['Language_Full'] = df2['Language'].map(LANG_MAP).fillna(df2['Language'])
        
        # Color Scale Fix: Clip at 90th percentile to differentiate colors
        fig2 = px.treemap(
            df2, path=['Language_Full'], values='Total_Comments',
            color='Avg_Likes', color_continuous_scale='Turbo',
            range_color=[0, df2['Avg_Likes'].quantile(0.9)],
            template='plotly_dark', height=750
        )
        st.plotly_chart(fig2, width='stretch')
        

# --- TAB 3: SENTIMENT & VIETNAMESE-READY WORDCLOUD ---
with tab3:
    st.header("Sentiment Dynamics")
    df3 = load_csv('TikTok_comments_with_sentiment.csv')
    if df3 is not None:
        selected_senti = st.selectbox("Select Sentiment:", df3['Sentiment_Type'].unique())
        
        # 3 Distinct Schemes
        schemes = {"Ironic Positive": "YlOrRd", "Generic Positive": "Greens", "Neutral": "Purples"}
        
        text = " ".join(df3[df3['Sentiment_Type'] == selected_senti]['Comments'].astype(str))
        if text.strip():
            sw = set(STOPWORDS).union({"video", "tiktok", "fyp", "watch", "videos"})
            wc = WordCloud(width=1000, height=500, background_color="black", 
                           font_path=FONT_PATH, # CRITICAL FOR VIETNAMESE
                           colormap=schemes.get(selected_senti, "viridis"),
                           regexp=r"\w[\w']+", # Improved regex for complex characters
                           collocations=False).generate(text)
            
            fig_wc, ax = plt.subplots(figsize=(10, 5))
            ax.imshow(wc, interpolation='bilinear')
            ax.axis("off")
            fig_wc.patch.set_facecolor('black')
            st.pyplot(fig_wc)

# --- TAB 4: FAN RADAR (Engagement Filter) ---
with tab4:
    st.header("Fan Radar: Loyalty vs. Authenticity")
    df4 = load_csv('user_behavior_summary.csv')
    if df4 is not None:
        # Filter: At least 5 comments to reduce clutter
        df_radar = df4[df4['total_comments_made'] >= 5].copy()
        df_radar['Total_Likes'] = df_radar['total_comments_made'] * df_radar['avg_comment_likes']
        
        search = st.text_input("🔍 Search & Highlight Username:")
        df_radar['Status'] = "Regular"
        if search:
            df_radar.loc[df_radar['Username'].str.contains(search, case=False, na=False), 'Status'] = "Target"

        fig4 = px.scatter(
            df_radar, x='loyalty_index', y='authenticity_score',
            size='total_comments_made', # Size based on quantity
            color='Status', color_discrete_map={"Regular": "#00f2ea", "Target": "#ff0050"},
            hover_name='Username', hover_data=['Total_Likes', 'total_comments_made'],
            template='plotly_dark', height=750
        )
        st.plotly_chart(fig4, width='stretch')