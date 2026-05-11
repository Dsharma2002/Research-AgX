from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from tools import web_search, scrape_url
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)

def build_search_agent():
    return create_agent(
        model=llm,
        tools=[web_search],
    )

def build_scrape_agent():
    return create_agent(
        model=llm,
        tools=[scrape_url],
    )

writer_agent_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert research writer. Write clear, structured, and insightful reports. "
                "Where possible, include specific statistics, numbers, dates, and empirical findings from the research. "
                "Prefer primary sources and research papers over blog posts."
                "Always include the full URL for every source, not just the publication name. "
                "For each key finding, include a brief critical counterpoint or limitation. "),
    ("human", """Write a detailed research report on the topic below.
     
    Topic: {topic}
    
    Research Gathered: {research}

    Previous Critic Feedback (if any): {feedback}
    
    Structure the report as:
    1. Introduction
    2. Key Findings (minimum 3 well-explained points)
    3. Conclusion
    4. Sources (list all URLs used for research)
    
    Be detailed, factual, and professional in your writing."""),
])

writer_chain = writer_agent_prompt | llm | StrOutputParser()

critic_agent_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert research critic. Evaluate the quality of the research report. Be honest and specific. "
                "Rate each criterion strictly as X/5 (e.g. 3/5) and provide an Overall Rating as X/5."),
    ("human", """Review the research report below and Evaluate it strictly.
    
    Research Report: {report}
    
    Assess the quality of the research report based on the following criteria:
    1. Is the report well-structured and organized?
    2. Are the key findings clearly presented and supported by evidence?
    3. Is the report written in a clear and concise manner?
    4. Are the sources cited properly and accurately reflected in the report?
    
    Rate the quality of the research report on a scale of 1 to 5, where 5 is the best and 1 is the worst."""),
])

critic_chain = critic_agent_prompt | llm | StrOutputParser()