import streamlit as st
import pandas as pd
import os
import plotly.express as px
import requests
from supabase import create_client
# --------------------------------
# PAGE SETTINGS
# --------------------------------

st.set_page_config(
    page_title="National Parks Explorer",
    page_icon="🏞️",
    layout="wide"
)

# --------------------------------
# SUPABASE CONNECTION + USER LOGIN
# --------------------------------

@st.cache_resource
def get_supabase_client():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )

try:
    supabase = get_supabase_client()
except Exception as exc:
    st.error("Supabase is not configured yet. Check the app's Streamlit Secrets settings.")
    st.stop()

if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    st.title("🌲 Welcome to National Parks Explorer")
    st.write("Create an account or log in to keep your own park progress and trips.")
    login_tab, signup_tab = st.tabs(["Log In", "Create Account"])

    with login_tab:
        with st.form("login_form"):
            login_email = st.text_input("Email address", key="login_email")
            login_password = st.text_input("Password", type="password", key="login_password")
            login_submit = st.form_submit_button("Log In", type="primary")
        if login_submit:
            try:
                auth_response = supabase.auth.sign_in_with_password({
                    "email": login_email.strip(),
                    "password": login_password
                })
                st.session_state.user = auth_response.user
                st.rerun()
            except Exception:
                st.error("We couldn't log you in. Check your email and password, and confirm your email address if you just signed up.")

    with signup_tab:
        with st.form("signup_form"):
            signup_email = st.text_input("Email address", key="signup_email")
            signup_password = st.text_input("Create a password", type="password", key="signup_password")
            signup_confirm = st.text_input("Confirm password", type="password", key="signup_confirm")
            signup_submit = st.form_submit_button("Create Account", type="primary")
        if signup_submit:
            if not signup_email.strip() or not signup_password:
                st.warning("Enter an email address and password.")
            elif signup_password != signup_confirm:
                st.warning("Your passwords don't match.")
            elif len(signup_password) < 6:
                st.warning("Please use a password with at least 6 characters.")
            else:
                try:
                    signup_response = supabase.auth.sign_up({
                        "email": signup_email.strip(),
                        "password": signup_password
                    })
                    if signup_response.session:
                        st.session_state.user = signup_response.user
                        st.success("Account created! You're logged in.")
                        st.rerun()
                    else:
                        st.success("Account created! Check your email for a confirmation link, then return here and log in.")
                except Exception as exc:
                    st.error(f"We couldn't create your account: {exc}")
    st.stop()

current_user_id = st.session_state.user.id
with st.sidebar:
    st.write(f"Signed in as **{st.session_state.user.email}**")
    if st.button("Log Out"):
        supabase.auth.sign_out()
        st.session_state.user = None
        st.rerun()

# --------------------------------
# HOMEPAGE DESIGN
# --------------------------------

st.markdown("""
<style>
.stApp {
    background-color: #F5F0E6;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
}

h1, h2, h3 {
    color: #244B35;
}

div[data-testid="stMetric"] {
    background-color: #E8E2D5;
    padding: 22px;
    border-radius: 16px;
    border-left: 5px solid #496B50;
    box-shadow: 0 3px 10px rgba(0,0,0,0.06);
}

div[data-testid="stMetricValue"] {
    color: #244B35;
    font-weight: 700;
}

.stButton > button {
    background-color: #355E3B;
    color: white;
    border-radius: 10px;
    border: none;
    padding: 8px 18px;
}

.stButton > button:hover {
    background-color: #244B35;
    color: white;
}

button[data-baseweb="tab"] {
    font-weight: 600;
    font-size: 15px;
}

div[data-testid="stExpander"] {
    background-color: #EEE8DC;
    border-radius: 12px;
    border: 1px solid #D8D0C2;
}

hr {
    border-color: #D8D0C2;
}
</style>
""", unsafe_allow_html=True)
# HOMEPAGE BANNER

st.markdown("""
<div style="
    background-color: #244B35;
    padding: 45px 25px;
    border-radius: 15px;
    text-align: center;
    margin-bottom: 25px;
">
    <h1 style="color: #F5F0E6; font-size: 48px; letter-spacing: 2px;">
        NATIONAL PARKS EXPLORER
    </h1>
    <p style="color: #E5D8B8; font-size: 19px;">
        Discover. Explore. Remember.
    </p>
    <p style="color: white; font-size: 15px;">
        Your personal guide to exploring all 63 U.S. National Parks.
    </p>
</div>
""", unsafe_allow_html=True)

st.write("")
# --------------------------------
# NATIONAL PARK DATABASE
# --------------------------------

parks = [
    ("Acadia", "Maine"),
    ("American Samoa", "American Samoa"),
    ("Arches", "Utah"),
    ("Badlands", "South Dakota"),
    ("Big Bend", "Texas"),
    ("Biscayne", "Florida"),
    ("Black Canyon of the Gunnison", "Colorado"),
    ("Bryce Canyon", "Utah"),
    ("Canyonlands", "Utah"),
    ("Capitol Reef", "Utah"),
    ("Carlsbad Caverns", "New Mexico"),
    ("Channel Islands", "California"),
    ("Congaree", "South Carolina"),
    ("Crater Lake", "Oregon"),
    ("Cuyahoga Valley", "Ohio"),
    ("Death Valley", "California"),
    ("Denali", "Alaska"),
    ("Dry Tortugas", "Florida"),
    ("Everglades", "Florida"),
    ("Gates of the Arctic", "Alaska"),
    ("Gateway Arch", "Missouri"),
    ("Glacier", "Montana"),
    ("Glacier Bay", "Alaska"),
    ("Grand Canyon", "Arizona"),
    ("Grand Teton", "Wyoming"),
    ("Great Basin", "Nevada"),
    ("Great Sand Dunes", "Colorado"),
    ("Great Smoky Mountains", "Tennessee"),
    ("Guadalupe Mountains", "Texas"),
    ("Haleakala", "Hawaii"),
    ("Hawaii Volcanoes", "Hawaii"),
    ("Hot Springs", "Arkansas"),
    ("Indiana Dunes", "Indiana"),
    ("Isle Royale", "Michigan"),
    ("Joshua Tree", "California"),
    ("Katmai", "Alaska"),
    ("Kenai Fjords", "Alaska"),
    ("Kings Canyon", "California"),
    ("Kobuk Valley", "Alaska"),
    ("Lake Clark", "Alaska"),
    ("Lassen Volcanic", "California"),
    ("Mammoth Cave", "Kentucky"),
    ("Mesa Verde", "Colorado"),
    ("Mount Rainier", "Washington"),
    ("New River Gorge", "West Virginia"),
    ("North Cascades", "Washington"),
    ("Olympic", "Washington"),
    ("Petrified Forest", "Arizona"),
    ("Pinnacles", "California"),
    ("Redwood", "California"),
    ("Rocky Mountain", "Colorado"),
    ("Saguaro", "Arizona"),
    ("Sequoia", "California"),
    ("Shenandoah", "Virginia"),
    ("Theodore Roosevelt", "North Dakota"),
    ("Virgin Islands", "U.S. Virgin Islands"),
    ("Voyageurs", "Minnesota"),
    ("White Sands", "New Mexico"),
    ("Wind Cave", "South Dakota"),
    ("Wrangell-St. Elias", "Alaska"),
    ("Yellowstone", "Wyoming"),
    ("Yosemite", "California"),
    ("Zion", "Utah")
]
# Coordinates for national parks

park_coordinates = {
    "Acadia": (44.3386, -68.2733),
    "American Samoa": (-14.2583, -170.6833),
    "Arches": (38.7331, -109.5925),
    "Badlands": (43.8554, -102.3397),
    "Big Bend": (29.2500, -103.2500),
    "Biscayne": (25.4824, -80.2083),
    "Black Canyon of the Gunnison": (38.5754, -107.7416),
    "Bryce Canyon": (37.5930, -112.1871),
    "Canyonlands": (38.3269, -109.8783),
    "Capitol Reef": (38.3670, -111.2615),
    "Carlsbad Caverns": (32.1479, -104.5567),
    "Channel Islands": (34.0069, -119.7785),
    "Congaree": (33.7948, -80.7821),
    "Crater Lake": (42.8684, -122.1685),
    "Cuyahoga Valley": (41.2808, -81.5678),
    "Death Valley": (36.5054, -117.0794),
    "Denali": (63.1148, -151.1926),
    "Dry Tortugas": (24.6285, -82.8732),
    "Everglades": (25.2866, -80.8987),
    "Gates of the Arctic": (67.7800, -153.3000),
    "Gateway Arch": (38.6247, -90.1848),
    "Glacier": (48.7596, -113.7870),
    "Glacier Bay": (58.6658, -136.9002),
    "Grand Canyon": (36.2679, -112.3535),
    "Grand Teton": (43.7904, -110.6818),
    "Great Basin": (38.9833, -114.3000),
    "Great Sand Dunes": (37.7916, -105.5943),
    "Great Smoky Mountains": (35.6118, -83.4895),
    "Guadalupe Mountains": (31.9230, -104.8855),
    "Haleakala": (20.7204, -156.1552),
    "Hawaii Volcanoes": (19.4194, -155.2885),
    "Hot Springs": (34.5217, -93.0424),
    "Indiana Dunes": (41.6533, -87.0524),
    "Isle Royale": (48.0115, -88.8278),
    "Joshua Tree": (33.8734, -115.9010),
    "Katmai": (58.5000, -155.0000),
    "Kenai Fjords": (59.8000, -149.5000),
    "Kings Canyon": (36.8879, -118.5551),
    "Kobuk Valley": (67.3550, -159.2000),
    "Lake Clark": (60.9700, -153.4200),
    "Lassen Volcanic": (40.4977, -121.4207),
    "Mammoth Cave": (37.1862, -86.1005),
    "Mesa Verde": (37.2309, -108.4618),
    "Mount Rainier": (46.8523, -121.7603),
    "New River Gorge": (38.0690, -81.0820),
    "North Cascades": (48.7718, -121.2985),
    "Olympic": (47.8021, -123.6044),
    "Petrified Forest": (34.9099, -109.8068),
    "Pinnacles": (36.4906, -121.1825),
    "Redwood": (41.2132, -124.0046),
    "Rocky Mountain": (40.3428, -105.6836),
    "Saguaro": (32.2967, -111.1666),
    "Sequoia": (36.4864, -118.5658),
    "Shenandoah": (38.2928, -78.6796),
    "Theodore Roosevelt": (46.9789, -103.5387),
    "Virgin Islands": (18.3420, -64.7830),
    "Voyageurs": (48.4837, -92.8388),
    "White Sands": (32.7791, -106.1710),
    "Wind Cave": (43.5724, -103.4416),
    "Wrangell-St. Elias": (61.7104, -142.9857),
    "Yellowstone": (44.4280, -110.5885),
    "Yosemite": (37.8651, -119.5383),
    "Zion": (37.2982, -113.0263)
}
# --------------------------------
# LOAD THIS USER'S PARK DATA FROM SUPABASE
# --------------------------------

try:
    park_response = (
        supabase.table("park_progress")
        .select("park_name, visited, date_visited, notes, favorite")
        .eq("user_id", current_user_id)
        .execute()
    )
    saved_rows = park_response.data or []
except Exception as exc:
    st.error(f"Couldn't load your park progress: {exc}")
    st.stop()

saved_parks = pd.DataFrame(saved_rows)
df = pd.DataFrame(parks, columns=["Park", "State"])
df["Visited"] = False
df["Date Visited"] = ""
df["Notes"] = ""
df["Favorite"] = False

if not saved_parks.empty:
    saved_parks = saved_parks.rename(columns={
        "park_name": "Park",
        "date_visited": "Date Visited",
        "visited": "Visited",
        "notes": "Notes",
        "favorite": "Favorite"
    })
    saved_parks["Date Visited"] = saved_parks["Date Visited"].fillna("").astype(str)
    saved_parks["Notes"] = saved_parks["Notes"].fillna("").astype(str)
    df = df.set_index("Park")
    saved_parks = saved_parks.set_index("Park")
    for column in ["Visited", "Date Visited", "Notes", "Favorite"]:
        if column in saved_parks.columns:
            df.loc[saved_parks.index, column] = saved_parks[column]
    df = df.reset_index()

df["Visited"] = df["Visited"].fillna(False).astype(bool)
df["Favorite"] = df["Favorite"].fillna(False).astype(bool)
df["Date Visited"] = df["Date Visited"].fillna("").astype(str)
df["Notes"] = df["Notes"].fillna("").astype(str)

# --------------------------------
# --------------------------------
# MAIN NAVIGATION
# --------------------------------

home_tab, tracker_tab, gallery_tab, favorites_tab, stats_tab, trips_tab = st.tabs([
    "🏠 Home",
    "🗺️ Park Tracker",
    "📸 Photo Gallery",
    "⭐ Favorites",
    "📊 Statistics",
    "✈️ Trip Planner"
])

with home_tab:
    # TITLE AND INTRODUCTION
    # --------------------------------

    st.title("🏞️ National Parks Explorer")

    st.subheader("My Journey to All 63 National Parks")

    st.write(
        "63 national parks. Countless adventures. "
        "One bucket list."
    )

    st.divider()

# --------------------------------
    # DASHBOARD STATISTICS
    # --------------------------------

    total = len(df)
    visited = int(df["Visited"].sum())
    remaining = total - visited
    progress = visited / total

    col1, col2, col3 = st.columns(3)

    col1.metric("🏞️ Total Parks", total)
    col2.metric("✅ Parks Visited", visited)
    col3.metric("🗺️ Remaining", remaining)

    st.subheader("My Progress")

    st.progress(progress)

    st.write(f"**{progress:.1%} of my bucket list completed!**")

    st.divider()

# --------------------------------
with tracker_tab:
    # PARK TRACKER
    # --------------------------------

    st.subheader("My National Park Tracker")

    st.write(
        "Check off parks you've visited, "
        "record your visit dates, and add personal notes."
    )

        # SEARCH AND FILTER PARKS
    st.subheader("🔎 Find a National Park")

    col1, col2, col3 = st.columns(3)

    with col1:
        search = st.text_input("Search by park name")

    with col2:
        state_filter = st.selectbox(
            "Filter by State",
            ["All States"] + sorted(df["State"].unique().tolist())
        )

    with col3:
        visit_filter = st.selectbox(
            "Visit Status",
            ["All Parks", "Visited", "Not Visited"]
        )

    filtered_df = df.copy()

    if search:
        filtered_df = filtered_df[
            filtered_df["Park"].str.contains(
                search, case=False, na=False
            )
        ]

    if state_filter != "All States":
        filtered_df = filtered_df[
            filtered_df["State"] == state_filter
        ]

    if visit_filter == "Visited":
        filtered_df = filtered_df[filtered_df["Visited"] == True]

    elif visit_filter == "Not Visited":
        filtered_df = filtered_df[filtered_df["Visited"] == False]

    st.write(f"Showing {len(filtered_df)} parks")
    edited_table = st.data_editor(
        filtered_df,
        hide_index=True,
        use_container_width=True,
        disabled=["Park", "State"],
        key="park_editor",
        column_config={
            "Park": st.column_config.TextColumn("National Park"),
            "State": st.column_config.TextColumn("Location"),
            "Visited": st.column_config.CheckboxColumn(
                "Visited?",
                default=False
            ),
            "Date Visited": st.column_config.TextColumn(
                "Date Visited",
                help="Enter date as MM/DD/YYYY"
            ),
            "Notes": st.column_config.TextColumn(
        "My Notes",
        help="Write about your experience!"
    ),

    "Favorite": st.column_config.CheckboxColumn(
        "⭐ Favorite",
        default=False
    )
        }
    )

    # --------------------------------
    # SAVE PROGRESS TO THIS USER'S SUPABASE RECORDS
    # --------------------------------
    if st.button("💾 Save My Progress", type="primary"):
        try:
            records = []
            for _, row in edited_table.iterrows():
                records.append({
                    "user_id": current_user_id,
                    "park_name": row["Park"],
                    "visited": bool(row["Visited"]),
                    "date_visited": str(row["Date Visited"]) if row["Date Visited"] else None,
                    "notes": str(row["Notes"]),
                    "favorite": bool(row["Favorite"])
                })
            if records:
                supabase.table("park_progress").upsert(
                    records, on_conflict="user_id,park_name"
                ).execute()
            st.success("Your national park progress has been saved to your account!")
            st.rerun()
        except Exception as exc:
            st.error(f"Couldn't save your progress: {exc}")

edited_df = df.copy()

# --------------------------------
# FOOTER
# --------------------------------

st.write(
    "🌲 Here's to exploring all 63 U.S. National Parks!"
)
# --------------------------------
# INTERACTIVE NATIONAL PARK MAP
# --------------------------------

st.divider()

st.header("🗺️ Explore the National Parks")

map_df = edited_df.copy()

map_df["Latitude"] = map_df["Park"].map(
    lambda park: park_coordinates.get(park, (None, None))[0]
)

map_df["Longitude"] = map_df["Park"].map(
    lambda park: park_coordinates.get(park, (None, None))[1]
)

map_df = map_df.dropna(
    subset=["Latitude", "Longitude"]
)

map_df["Status"] = map_df["Visited"].map({
    True: "Visited",
    False: "Not Visited"
})

fig = px.scatter_geo(
    map_df,
    lat="Latitude",
    lon="Longitude",
    color="Status",
    hover_name="Park",
    hover_data=["State"],
    scope="usa",
    color_discrete_map={
        "Visited": "green",
        "Not Visited": "red"
    },
    title="My National Parks Adventure"
)

fig.update_layout(
    height=650,
    geo=dict(
        showland=True,
        landcolor="#EEE8D5",
        showocean=True,
        oceancolor="#DCEAF0",
        showlakes=True,
        lakecolor="#DCEAF0"
    )
)

st.plotly_chart(
    fig,
    use_container_width=True
)
# --------------------------------
# VINTAGE NATIONAL PARKS BUCKET LIST
# --------------------------------

st.divider()

st.header("🌲 The Great American Adventure")

st.write(
    "A visual bucket list of all 63 U.S. National Parks. "
    "Every park has a story. Every visit is an adventure."
)

# Calculate progress
visited_parks = edited_df[edited_df["Visited"] == True]
unvisited_parks = edited_df[edited_df["Visited"] == False]

# Display progress
st.markdown(
    """
    <div style="
        background-color: #F3EBDD;
        padding: 25px;
        border-radius: 12px;
        text-align: center;
        border: 2px solid #A68A64;
    ">
        <h2 style="color: #34513A;">
            MY NATIONAL PARKS BUCKET LIST
        </h2>
        <p style="color: #765C40;">
            63 Parks • 1 Adventure • A Lifetime of Memories
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

st.write("")

# Show completed parks
st.subheader("⭐ Parks I've Explored")

if len(visited_parks) == 0:
    st.info("Your adventure is just beginning! Visit your first park to see it here.")
else:
    cols = st.columns(3)

    for index, (_, park) in enumerate(visited_parks.iterrows()):
        with cols[index % 3]:
            st.markdown(
                f"""
                <div style="
                    background-color: #E6E1D3;
                    padding: 15px;
                    border-radius: 10px;
                    margin-bottom: 10px;
                    border-left: 5px solid #456B45;
                ">
                    <h4 style="color: #34513A;">
                        ✓ {park['Park']}
                    </h4>
                    <p style="color: #765C40;">
                        {park['State']}
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

# Show remaining parks
st.subheader("🧭 Still on My Bucket List")

with st.expander("Explore parks I haven't visited yet"):
    for _, park in unvisited_parks.iterrows():
        st.write(f"🌲 {park['Park']} — {park['State']}")

st.divider()

st.markdown(
    """
    <p style="
        text-align: center;
        color: #456B45;
        font-style: italic;
        font-size: 18px;
    ">
        "The mountains are calling, and I must go."
    </p>
    """,
    unsafe_allow_html=True
)
# --------------------------------
# NATIONAL PARKS PHOTO GALLERY
# --------------------------------

with gallery_tab:
    st.divider()

    st.header("📸 Explore the National Parks")

    st.write(
        "Discover America's national parks through photographs "
        "and learn a little more about each destination."
    )

    # Select a national park
    selected_park = st.selectbox(
        "Choose a National Park",
        edited_df["Park"].tolist()
    )

    # Find park information using Wikipedia
    @st.cache_data(ttl=86400)
    def get_park_information(park_name):

        search_name = park_name + " National Park"

        if park_name == "American Samoa":
            search_name = "National Park of American Samoa"

        url = "https://en.wikipedia.org/w/api.php"

        params = {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": search_name,
            "gsrlimit": 1,
            "prop": "pageimages|extracts",
            "piprop": "original|thumbnail",
            "pithumbsize": 1200,
            "exintro": True,
            "explaintext": True,
            "exsentences": 3
        }

        try:
            response = requests.get(
                url,
                params=params,
                headers={"User-Agent": "NationalParksExplorer/1.0"},
                timeout=15
            )

            response.raise_for_status()

            data = response.json()

            pages = data.get("query", {}).get("pages", {})

            if not pages:
                return None, None, None, None

            page = next(iter(pages.values()))

            image_url = (
                page.get("original", {}).get("source")
                or page.get("thumbnail", {}).get("source")
            )

            description = page.get(
                "extract",
                "Explore this beautiful national park!"
            )

            page_url = (
                "https://en.wikipedia.org/wiki/"
                + requests.utils.quote(page["title"].replace(" ", "_"))
            )

            return image_url, description, page["title"], page_url

        except requests.RequestException:
            return None, None, None, None


    # Display selected park
    park_info = edited_df[
        edited_df["Park"] == selected_park
    ].iloc[0]

    image_url, description, page_title, page_url = (
        get_park_information(selected_park)
    )

    st.subheader(f"🏞️ {selected_park} National Park")

    st.caption(f"Location: {park_info['State']}")

    if image_url:

        st.image(
            image_url,
            use_container_width=True
        )

        st.write(description)

        st.link_button(
            "Learn More About This Park",
            page_url
        )

    else:
        st.info(
            "We couldn't find a photograph right now. "
            "Try selecting another park."
        )

    st.divider()

    # Personal visit information
    st.subheader("📝 My Memories")

    if park_info["Visited"]:

        st.success("You've visited this park!")

        st.write(
            f"**Date Visited:** {park_info['Date Visited']}"
        )

        st.write(
            f"**My Notes:** {park_info['Notes']}"
        )

    else:

        st.info("This park is still on your bucket list!")
    # --------------------------------
with favorites_tab:

    st.divider()

    st.header("⭐ My Favorite National Parks")

    st.write("Your personal collection of favorite parks.")

    favorite_parks = df[df["Favorite"] == True]

    if not favorite_parks.empty:

        st.success(f"You have {len(favorite_parks)} favorite parks!")

        st.dataframe(
            favorite_parks[
                ["Park", "State", "Favorite", "Visited", "Date Visited", "Notes"]
            ],
            hide_index=True,
            use_container_width=True
        )

    else:

        st.info(
            "You haven't selected any favorite parks yet. "
            "Go to the Park Tracker and check the Favorite box!"
        )
with stats_tab:
    # TRAVEL STATISTICS DASHBOARD
    # --------------------------------

    st.divider()

    st.header("📊 My Travel Statistics")

    # Separate visited and unvisited parks
    visited_parks = edited_df[edited_df["Visited"] == True].copy()

    # Convert visit dates into dates Python can understand
    visited_parks["Date Visited"] = pd.to_datetime(
        visited_parks["Date Visited"],
        errors="coerce"
    )

    # Display statistics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Parks Visited", len(visited_parks))

    with col2:
        st.metric(
            "States Explored",
            visited_parks["State"].nunique()
        )

    with col3:
        st.metric(
            "Parks Remaining",
            len(edited_df) - len(visited_parks)
        )

       # ACHIEVEMENTS AND MILESTONES
    st.divider()
    st.subheader("🏅 Achievements & Milestones")

    total_visited = len(visited_parks)

    milestones = [
        (1, "First Steps", "Visit your first national park!", "🌱"),
        (5, "Explorer", "Visit 5 national parks.", "🥾"),
        (10, "Adventure Seeker", "Visit 10 national parks.", "🧭"),
        (15, "Park Enthusiast", "Visit 15 national parks.", "🏕️"),
        (25, "Quarter Century", "Visit 25 national parks.", "⭐"),
        (40, "Wildlife Wanderer", "Visit 40 national parks.", "🦬"),
        (50, "Master Explorer", "Visit 50 national parks.", "🏔️"),
        (63, "National Parks Legend", "Visit all 63 national parks!", "🏆")
    ]

    achievement_columns = st.columns(2)

    for index, (goal, title, description, icon) in enumerate(milestones):

        with achievement_columns[index % 2]:

            if total_visited >= goal:
                card_background = "#E3EBDD"
                card_border = "#496B50"
                text_color = "#244B35"
                status = "🏅 UNLOCKED"
            else:
                card_background = "#EEE8DC"
                card_border = "#C8BFAF"
                text_color = "#777368"
                status = "🔒 LOCKED"

            st.markdown(f"""
            <div style="
                background-color: {card_background};
                border-left: 5px solid {card_border};
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 12px;
                min-height: 105px;
            ">
                <div style="color: {text_color}; font-weight: 700; font-size: 17px;">
                    {icon} {title}
                </div>
                <div style="color: {text_color}; font-size: 13px; margin-top: 5px;">
                    {status}
                </div>
                <div style="color: {text_color}; margin-top: 10px;">
                    {description}
                </div>
            </div>
            """, unsafe_allow_html=True)
    # Progress toward the next milestone
    next_milestone = next(
        (m for m in milestones if total_visited < m[0]),
        None
    )

    if next_milestone:
        goal, title, description, icon = next_milestone

        st.write(f"### 🎯 Next Goal: {title}")
        st.progress(total_visited / goal)
        st.caption(f"{total_visited} of {goal} parks visited")

    else:
        st.balloons()
        st.success("You've visited all 63 national parks! You're a legend!")
    # Progress by state
    st.subheader("🗺️ Parks Visited by State")

    if not visited_parks.empty:

        state_counts = (
            visited_parks.groupby("State")
            .size()
            .reset_index(name="Parks Visited")
            .sort_values("Parks Visited", ascending=True)
        )

        fig = px.bar(
            state_counts,
            x="Parks Visited",
            y="State",
            orientation="h",
            title="My National Parks by State",
            text="Parks Visited"
        )

        st.plotly_chart(fig, use_container_width=True)
                # Parks visited by region
        state_regions = {
            "Maine": "Northeast",
            "Pennsylvania": "Northeast",
            "California": "West",
            "Utah": "West",
            "Colorado": "West",
            "Wyoming": "West",
            "Montana": "West",
            "Washington": "West",
            "Oregon": "West",
            "Idaho": "West",
            "Nevada": "West",
            "Alaska": "Alaska & Pacific",
            "Hawaii": "Alaska & Pacific",
            "American Samoa": "Alaska & Pacific",
            "Florida": "Southeast",
            "Georgia": "Southeast",
            "North Carolina": "Southeast",
            "South Carolina": "Southeast",
            "Tennessee": "Southeast",
            "Kentucky": "Southeast",
            "Virginia": "Southeast",
            "Arkansas": "Southeast",
            "Texas": "Southwest",
            "Arizona": "Southwest",
            "New Mexico": "Southwest",
            "Oklahoma": "Southwest",
            "Michigan": "Midwest",
            "Minnesota": "Midwest",
            "South Dakota": "Midwest",
            "North Dakota": "Midwest",
            "Missouri": "Midwest",
            "Ohio": "Midwest"
        }

        visited_parks["Region"] = visited_parks["State"].map(
            state_regions
        ).fillna("Other")

        region_counts = (
            visited_parks.groupby("Region")
            .size()
            .reset_index(name="Parks Visited")
        )

        st.subheader("🗺️ My Adventures by Region")

        region_fig = px.pie(
            region_counts,
            names="Region",
            values="Parks Visited",
            title="Where I've Explored",
            hole=0.4
        )

        st.plotly_chart(
            region_fig,
            use_container_width=True
        )

    else:
        st.info("Your statistics will appear here once you visit your first park!")

    # Visit timeline
    st.subheader("📅 My Visiting Timeline")

    dated_parks = visited_parks.dropna(
        subset=["Date Visited"]
    )

    if not dated_parks.empty:

        timeline = (
            dated_parks.groupby("Date Visited")
            .size()
            .reset_index(name="Parks Visited")
            .sort_values("Date Visited")
        )

        fig = px.line(
            timeline,
            x="Date Visited",
            y="Parks Visited",
            markers=True,
            title="My National Park Adventures Over Time"
        )

        st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("Add visit dates to your parks to see your travel timeline!")
        # --------------------------------
# NATIONAL PARKS TRIP PLANNER
# --------------------------------

with trips_tab:
    st.divider()
    st.header("✈️ Plan My Next Adventure")
    st.write("Organize the national parks you want to visit on future trips!")

    st.subheader("➕ Create a New Trip")
    with st.form("new_trip_form"):
        trip_name = st.text_input("Trip Name")
        selected_parks = st.multiselect(
            "Choose National Parks", edited_df["Park"].tolist()
        )
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date")
        with col2:
            end_date = st.date_input("End Date")
        trip_notes = st.text_area("Trip Notes")
        submitted = st.form_submit_button("Save Trip")

    if submitted:
        if trip_name.strip() and selected_parks:
            try:
                supabase.table("user_trips").insert({
                    "user_id": current_user_id,
                    "trip_name": trip_name.strip(),
                    "parks": ", ".join(selected_parks),
                    "start_date": str(start_date),
                    "end_date": str(end_date),
                    "notes": trip_notes
                }).execute()
                st.success("Your trip has been saved to your account!")
                st.rerun()
            except Exception as exc:
                st.error(f"Couldn't save your trip: {exc}")
        else:
            st.warning("Please enter a trip name and select at least one park.")

    st.subheader("🧳 My Upcoming Trips")
    try:
        trips_response = (
            supabase.table("user_trips")
            .select("id, trip_name, parks, start_date, end_date, notes")
            .eq("user_id", current_user_id)
            .order("start_date")
            .execute()
        )
        user_trips = trips_response.data or []
    except Exception as exc:
        st.error(f"Couldn't load your trips: {exc}")
        user_trips = []

    if user_trips:
        for trip in user_trips:
            with st.expander(f"🌎 {trip['trip_name']}"):
                st.write(f"**Parks:** {trip.get('parks') or ''}")
                st.write(f"**Start:** {trip.get('start_date') or ''}")
                st.write(f"**End:** {trip.get('end_date') or ''}")
                st.write(f"**Notes:** {trip.get('notes') or ''}")
                if st.button("Delete Trip", key=f"delete_trip_{trip['id']}"):
                    try:
                        supabase.table("user_trips").delete().eq(
                            "id", trip["id"]
                        ).eq("user_id", current_user_id).execute()
                        st.success("Trip deleted!")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Couldn't delete this trip: {exc}")
    else:
        st.info("You haven't planned any trips yet. Create your first one above!")
