# Implementation notes

## Data flow
Patient form -> input validation -> conservative emergency phrase screen -> LLMChain -> safe JSON parse -> schema validation -> streaming explanation -> results dashboard.

## Why the first version is not yet a RAG system
The supplied assignment evaluates symptom intake, prompt engineering, LLMChain, structured JSON, streaming and caching. It does not ask for document retrieval. RAG is reserved as a separately testable extension so that the required assignment is completed and demonstrable first.

## Safety limitations
This is not a validated clinical decision-support system. The phrase screen can miss emergencies and can flag phrases in irrelevant contexts. It must never be used to decide that a person is safe.
