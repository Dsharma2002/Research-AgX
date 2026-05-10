from agents import build_search_agent, build_scrape_agent, writer_chain, critic_chain

def run_pipeline(topic: str) -> dict:
    state = {}
    
    print("\n ====== Search Agent ====== \n")
    print("Step 1 - search agent is working")
    print("\n ========================== \n")
    
    search_agent = build_search_agent()
    search_result = search_agent.invoke({
        "messages": [("user", f"Find recent, reliable, and detailed information about {topic}.")],
    })
    state["search_result"] = search_result["messages"][-1].content
    print("\n Search Result: \n", state["search_result"])
    
    print("\n ====== Scrape Agent ====== \n")
    print("Step 2 - scrape agent is working")
    print("\n ========================== \n")

    scrape_agent = build_scrape_agent()
    scrape_agent_result = scrape_agent.invoke({
        "messages": [("user",
                     f"Based on the searh results about '{topic}', "
                     f"pick the most relevant URL and scrape it for deep reading.\n\n"
                     f"Search Result: \n{state['search_result'][:800]}\n\n"
        )]
    })
    state["scraped_content"] = scrape_agent_result["messages"][-1].content
    print("\n Scraped Content: \n", state["scraped_content"])
    
    print("\n ========= Writer ========= \n")
    print("Step 3 - writer is working")
    print("\n ========================== \n")
    
    research_combined = (
        f"SEARCH RESULTS: \n {state['search_result']}\n\n",
        f"DETAILED SCRAPED CONTENT: \n {state['scraped_content']}\n\n",
    )
    
    state["report"] = writer_chain.invoke({
        "topic": topic,
        "research": research_combined,
    })
    print("\n Report: \n", state["report"])
    
    print("\n ========= Critic ========= \n")
    print("Step 4 - critic is working")
    print("\n ========================== \n")
    
    state["critic_score"] = critic_chain.invoke({
        "report": state["report"],
    })
    print("\n Critic Score: \n", state["critic_score"])
    
    return state


if __name__ == "__main__":
    topic = input("\n Enter a research topic: ")
    run_pipeline(topic)
    
