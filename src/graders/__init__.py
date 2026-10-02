"""
Registry for the three grading strategies. Everything else in the project
(graph.py, run_comparison.py, gold_labels.py) goes through get_grader()
rather than importing a specific grader module directly -- this is what
makes the strategies swappable.

Every grader module exposes the same two functions:
    score_chunk(query: str, chunk: Chunk) -> float      # 0-1 relevance score
    grade_chunks(query: str, chunks: list[Chunk]) -> (list[Chunk], float)
"""
from . import llm_grader, crossencoder_grader, threshold_grader

GRADERS = {
    "llm": llm_grader,
    "crossencoder": crossencoder_grader,
    "threshold": threshold_grader,
}


def get_grader(name: str):
    if name not in GRADERS:
        raise ValueError(f"Unknown grader '{name}'. Choose from {list(GRADERS)}")
    return GRADERS[name]
