from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import re
import asyncio

from agents import build_search_agent, build_scrape_agent, writer_chain, critic_chain

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ResearchRequest(BaseModel):
    topic: str

@app.post("/api/research")
async def research(req: ResearchRequest):
    async def event_stream():
        topic = req.topic
        state = {}

        def send_event(step, status, data=None, label=None):
            payload = {"step": step, "status": status}
            if data is not None:
                payload["data"] = data
            if label is not None:
                payload["label"] = label
            return f"data: {json.dumps(payload)}\n\n"

        try:
            # Step 1: Search
            yield send_event("search", "running", label="🔍 Step 1 — Search Agent is working...")
            await asyncio.sleep(0.1)
            search_agent = build_search_agent()
            search_result = search_agent.invoke({
                "messages": [("user", f"Find recent, reliable, and detailed information about {topic} from 2025 or 2026 only.")],
            })
            state["search_result"] = search_result["messages"][-1].content
            yield send_event("search", "complete", data=state["search_result"], label="✅ Step 1 — Search Agent done")

            # Step 2: Scrape
            yield send_event("scrape", "running", label="🕷️ Step 2 — Scrape Agent is working...")
            await asyncio.sleep(0.1)
            scrape_agent = build_scrape_agent()
            scrape_result = scrape_agent.invoke({
                "messages": [("user",
                    f"Based on the search results about '{topic}', "
                    f"pick the TOP 3 most relevant URLs and scrape each one for deep reading.\n\n"
                    f"Search Result:\n{state['search_result'][:800]}\n\n"
                )]
            })
            state["scraped_content"] = scrape_result["messages"][-1].content
            yield send_event("scrape", "complete", data=state["scraped_content"], label="✅ Step 2 — Scrape Agent done")

            # Step 3: Writer
            research_combined = (
                f"SEARCH RESULTS:\n{state['search_result']}\n\n"
                f"DETAILED SCRAPED CONTENT:\n{state['scraped_content']}\n\n"
            )
            yield send_event("write", "running", label="✍️ Step 3 — Writer is working...")
            await asyncio.sleep(0.1)
            state["report"] = writer_chain.invoke({
                "topic": topic,
                "research": research_combined,
                "feedback": "No feedback yet.",
            })
            yield send_event("write", "complete", data=state["report"], label="✅ Step 3 — Writer done")

            # Step 4: Critic
            yield send_event("critic", "running", label="🧐 Step 4 — Critic is reviewing...")
            await asyncio.sleep(0.1)
            state["critic_score"] = critic_chain.invoke({"report": state["report"]})
            yield send_event("critic", "complete", data=state["critic_score"], label="✅ Step 4 — Critic done")

            # Step 5: Reflection Loop
            MAX_REWRITES = 2
            rewrites = 0

            while rewrites < MAX_REWRITES:
                scores = re.findall(r'\b([1-5])(?:\.\d+)?(?:\s*\/\s*5)', state["critic_score"])
                avg_score = sum(float(s) for s in scores) / len(scores) if scores else 5

                if avg_score >= 4:
                    break

                yield send_event(f"reflection_{rewrites+1}", "running", label=f"🔁 Critic score {avg_score:.1f}/5 — rewriting (attempt {rewrites + 1} of {MAX_REWRITES})...")
                
                # Rewrite
                yield send_event(f"rewrite_{rewrites+1}", "running", label=f"✍️ Rewrite {rewrites + 1} — Writer incorporating feedback...")
                await asyncio.sleep(0.1)
                state["report"] = writer_chain.invoke({
                    "topic": topic,
                    "research": research_combined,
                    "feedback": state["critic_score"],
                })
                yield send_event(f"rewrite_{rewrites+1}", "complete", data=state["report"], label=f"✅ Rewrite {rewrites + 1} done")

                # Recritic
                yield send_event(f"recritic_{rewrites+1}", "running", label=f"🧐 Re-evaluating after rewrite {rewrites + 1}...")
                await asyncio.sleep(0.1)
                state["critic_score"] = critic_chain.invoke({"report": state["report"]})
                yield send_event(f"recritic_{rewrites+1}", "complete", data=state["critic_score"], label=f"✅ Re-evaluation {rewrites + 1} done")

                yield send_event(f"reflection_{rewrites+1}", "complete", label=f"✅ Reflection {rewrites + 1} complete")
                
                rewrites += 1

            # Final Result
            yield send_event("done", "complete", data={"report": state["report"], "critic_score": state["critic_score"]})
        except Exception as e:
            yield send_event("error", "failed", data=str(e), label=f"❌ Error: {str(e)}")

    return StreamingResponse(event_stream(), media_type="text/event-stream")
