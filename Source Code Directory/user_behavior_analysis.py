import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
import os

# --- Language Mapping ---
LANG_MAP = {
    'en': 'English', 'vi': 'Vietnamese', 'zh-cn': 'Chinese (Simplified)',
    'ko': 'Korean', 'id': 'Indonesian', 'ms': 'Malay', 'th': 'Thai',
    'tl': 'Tagalog', 'ja': 'Japanese', 'hi': 'Hindi', 'fr': 'French',
    'so': 'Somali', 'ar': 'Arabic', 'pt': 'Portuguese'
}

# --- Font Path for WordCloud (Fixes Square Boxes for Unicode) ---
# Windows: 'C:/Windows/Fonts/simsun.ttc' or 'msgothic.ttc'
# Mac: '/Library/Fonts/Arial Unicode.ttf'
FONT_PATH = 'C:/Windows/Fonts/simsun.ttc' if os.path.exists('C:/Windows/Fonts/simsun.ttc') else None

@st.cache_data
def load_csv_data(filepath):
    if not os.path.exists(filepath):
        return None
    return pd.read_csv(filepath)

st.set_page_config(page_title="TikTok Engagement Dashboard", layout="wide")
st.title("📱 TikTok Engagement & Sentiment Dashboard")

tab1, tab2, tab3, tab4 = st.tabs([
    "1. Viral Dashboard", 
    "2. Cross-Cultural Resonance", 
    "3. Negative is Positive", 
    "4. Fan Radar"
])

# --- TAB 1: VIRAL DASHBOARD (Meme Lifecycle) ---
with tab1:
    st.header("Meme Lifecycle: Frequency & Engagement")
    df1 = load_csv_data('meme_time_series.csv')
    
    if df1 is not None:
        df1['start_date'] = pd.to_datetime(df1['week'].str.split('/').str[0])
        df1 = df1.sort_values('start_date')

        fig1 = go.Figure()
        buzzwords = df1['buzzword'].unique()

        for meme in buzzwords:
            meme_data = df1[df1['buzzword'] == meme]
            fig1.add_trace(go.Scatter(
                x=meme_data['start_date'],
                y=meme_data['frequency'],
                mode='lines+markers',
                name=meme,
                line_shape='spline',
                line=dict(width=2),
                marker=dict(size=6),
                customdata=meme_data[['avg_likes', 'week']],
                hovertemplate=(
                    "<b>%{text}</b><br>Date: %{x|%Y-%m-%d}<br>" +
                    "Freq: %{y}<br>Avg Likes: %{customdata[0]:.0f}<extra></extra>"
                ),
                text=[meme] * len(meme_data)
            ))

        fig1.update_layout(
            template='plotly_dark',
            hovermode='closest',
            updatemenus=[
                dict(
                    type="dropdown", x=1.15, y=1, showactive=True, active=0,
                    bgcolor="#333333", font=dict(color="white"),
                    buttons=list([dict(label="Show All", method="update", args=[{"visible": [True] * len(buzzwords)}, {"title": "All Trends"}])] +
                                 [dict(label=meme, method="update", args=[{"visible": [m == meme for m in buzzwords]}, {"title": f"Trend: {meme}"}]) for meme in buzzwords])
                ),
                dict(
                    type="buttons", direction="left", x=0, y=1.1, active=0,
                    bgcolor="#444444", font=dict(color="white"),
                    buttons=list([
                        dict(label="Normal Scale", method="relayout", args=[{"yaxis.type": "linear"}]),
                        dict(label="Log Scale (See details)", method="relayout", args=[{"yaxis.type": "log"}])
                    ])
                )
            ],
            xaxis=dict(title="Timeline", rangeslider=dict(visible=True), type="date"),
            yaxis=dict(title="Frequency")
        )
        st.plotly_chart(fig1, width='stretch')

# --- TAB 2: CROSS-CULTURAL RESONANCE ---
with tab2:
    st.header("Cultural Engagement by Language")
    df2 = load_csv_data('stage1_language_engagement.csv')
    
    if df2 is not None:
        df2 = df2[df2['Total_Comments'] > 0].copy()
        df2['Language_Full'] = df2['Language'].map(LANG_MAP).fillna(df2['Language'])
        
        # Treemap with high-contrast scale and outlier clipping
        fig2 = px.treemap(
            df2,
            path=['Language_Full'],
            values='Total_Comments',
            color='Avg_Likes',
            color_continuous_scale='Electric',
            range_color=[0, df2['Avg_Likes'].quantile(0.85)], # Spreads color across non-outliers
            title='Comment Volume by Language (Size) and Engagement (Color)',
            template='plotly_dark', height=750
        )
        st.plotly_chart(fig2, width='stretch')

# --- TAB 3: NEGATIVE IS POSITIVE ---
with tab3:
    st.header("Sentiment & Aesthetic Fatigue")
    df3 = load_csv_data('TikTok_comments_with_sentiment.csv')
    
    if df3 is not None:
        # Scatter Plot - Fixed column names and log scale
        df3_clean = df3[df3['Comment Likes'] > 0].copy()
        fig3 = px.scatter(
            df3_clean, x='Sentiment_Confidence', y='Comment Likes',
            color='Sentiment_Type', log_y=True,
            hover_data=['Comments'], 
            height=700, template='plotly_dark'
        )
        st.plotly_chart(fig3, width='stretch')

        # WordCloud with distinct color schemes per sentiment
        st.subheader("Word Cloud by Sentiment Type")
        selected_senti = st.selectbox("Select Sentiment:", df3['Sentiment_Type'].unique())
        
        schemes = {"Ironic Positive": "YlOrRd", "Generic Positive": "Greens", "Neutral": "Purples"}
        text = " ".join(df3[df3['Sentiment_Type'] == selected_senti]['Comments'].astype(str))
        
        if text.strip():
            sw = set(STOPWORDS).union({"video", "tiktok", "fyp", "watch", "videos"})
            wc = WordCloud(width=800, height=400, background_color="black", 
                           stopwords=sw, colormap=schemes.get(selected_senti, "viridis"),
                           font_path=FONT_PATH).generate(text)
            fig_wc, ax = plt.subplots()
            ax.imshow(wc, interpolation='bilinear')
            ax.axis("off")
            fig_wc.patch.set_facecolor('black')
            st.pyplot(fig_wc)

# --- TAB 4: FAN RADAR ---
with tab4:
    st.header("High-Engagement Fan Analysis")
    df4 = load_csv_data('user_behavior_summary.csv')
    
    if df4 is not None:
        # Filter: only show users with at least 5 comments
        df_radar = df4[df4['total_comments_made'] >= 5].copy()
        df_radar['total_likes_received'] = df_radar['total_comments_made'] * df_radar['avg_comment_likes']
        
        # Search & Highlight
        search_user = st.text_input("🔍 Highlight a specific username:")
        df_radar['Highlight'] = "Standard"
        if search_user:
            df_radar.loc[df_radar['Username'].str.contains(search_user, case=False, na=False), 'Highlight'] = "Target"

        fig4 = px.scatter(
            df_radar, x='loyalty_index', y='authenticity_score',
            size='total_comments_made', # Size based on volume
            color='Highlight',
            color_discrete_map={"Standard": "#00f2ea", "Target": "#ff0050"},
            hover_name='Username',
            hover_data={'total_likes_received': ':,.0f', 'total_comments_made': True},
            template='plotly_dark', height=750,
            title="Fan Radar: Loyalty vs. Authenticity (Bubble Size = Comment Count)"
        )
        st.plotly_chart(fig4, width='stretch')