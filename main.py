import streamlit as st
from agents import build_search_agent, build_scrape_agent, writer_chain, critic_chain

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Research AGX",
    page_icon="🔬",
    layout="wide",
)

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🔬 Research AGX")
st.caption("A multi-agent research pipeline: Search → Scrape → Write → Critique")
st.divider()

# ── Input ─────────────────────────────────────────────────────────────────────
topic = st.text_input(
    "Enter a research topic",
    placeholder="e.g. Impact of AI on healthcare in 2025",
)

run = st.button("Run Pipeline", type="primary", disabled=not topic)

# ── Pipeline ──────────────────────────────────────────────────────────────────
if run and topic:
    state = {}

    # Step 1 — Search
    status_bar = st.status("🔍 Step 1 — Search Agent is working...", expanded=True)
    with status_bar:
        st.write("Querying Tavily for recent, reliable sources...")
        search_agent = build_search_agent()
        search_result = search_agent.invoke({
            "messages": [("user", f"Find recent, reliable, and detailed information about {topic}.")],
        })
        state["search_result"] = search_result["messages"][-1].content
        st.write("✅ Search complete.")
    status_bar.update(label="✅ Step 1 — Search Agent done", state="complete", expanded=False)

    with st.expander("📄 Search Results", expanded=False):
        st.text(state["search_result"])

    # Step 2 — Scrape
    status_bar2 = st.status("🕷️ Step 2 — Scrape Agent is working...", expanded=True)
    with status_bar2:
        st.write("Picking the most relevant URL and scraping full content...")
        scrape_agent = build_scrape_agent()
        scrape_result = scrape_agent.invoke({
            "messages": [("user",
                f"Based on the search results about '{topic}', "
                f"pick the most relevant URL and scrape it for deep reading.\n\n"
                f"Search Result:\n{state['search_result'][:800]}\n\n"
            )]
        })
        state["scraped_content"] = scrape_result["messages"][-1].content
        st.write("✅ Scrape complete.")
    status_bar2.update(label="✅ Step 2 — Scrape Agent done", state="complete", expanded=False)

    with st.expander("🌐 Scraped Content", expanded=False):
        st.text(state["scraped_content"])

    # Step 3 — Writer
    status_bar3 = st.status("✍️ Step 3 — Writer is working...", expanded=True)
    with status_bar3:
        st.write("Synthesising research into a structured report...")
        research_combined = (
            f"SEARCH RESULTS:\n{state['search_result']}\n\n"
            f"DETAILED SCRAPED CONTENT:\n{state['scraped_content']}\n\n"
        )
        state["report"] = writer_chain.invoke({
            "topic": topic,
            "research": research_combined,
        })
        st.write("✅ Report written.")
    status_bar3.update(label="✅ Step 3 — Writer done", state="complete", expanded=False)

    # Step 4 — Critic
    status_bar4 = st.status("🧐 Step 4 — Critic is reviewing...", expanded=True)
    with status_bar4:
        st.write("Evaluating the report quality...")
        state["critic_score"] = critic_chain.invoke({
            "report": state["report"],
        })
        st.write("✅ Review complete.")
    status_bar4.update(label="✅ Step 4 — Critic done", state="complete", expanded=False)

    # ── Results ───────────────────────────────────────────────────────────────
    st.divider()
    st.subheader("📝 Research Report")
    st.markdown(state["report"])

    st.divider()
    st.subheader("🧐 Critic's Review")
    st.info(state["critic_score"])

    # Download
    st.download_button(
        label="⬇️ Download Report",
        data=state["report"],
        file_name=f"{topic[:40].replace(' ', '_')}_report.txt",
        mime="text/plain",
    )