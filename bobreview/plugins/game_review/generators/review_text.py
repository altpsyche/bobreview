"""
Enhanced LLM generators for game_review plugin.

Creates multiple content sections from minimal user input:
- Expanded review text
- Target audience ("People who like...")
- Similar game recommendations
- Expanded pros/cons
"""

from typing import Dict, List, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from bobreview.core.config import ReportConfig

from bobreview.services.llm.client import call_llm


def generate_full_review(
    data_points: List[Dict[str, Any]],
    stats: Dict[str, Any],
    config: "ReportConfig",
    _images_dir_rel: str = ""
) -> str:
    """
    Generate a professional expanded game review from user's brief notes.
    
    Takes user's quick review and expands it into professional paragraphs.
    """
    data = stats
    
    # Build scores section if provided
    scores = data.get('scores', {})
    scores_text = ""
    if scores:
        scores_text = f"""
CATEGORY SCORES (out of 10):
- Gameplay: {scores.get('gameplay', 'N/A')}
- Graphics: {scores.get('graphics', 'N/A')}
- Story: {scores.get('story', 'N/A')}
- Sound & Music: {scores.get('sound', 'N/A')}
- Value: {scores.get('value', 'N/A')}
"""
    
    # Build prompt from user's input
    prompt = f"""You are a professional video game reviewer. Expand the user's brief review into a professional, 
engaging 3-4 paragraph game review.

GAME: {data.get('name', 'Unknown Game')}
GENRE: {data.get('genre', 'Unknown')}

USER'S BRIEF REVIEW:
{data.get('my_review', 'No review provided.')}

WHAT THE USER LIKED:
{chr(10).join('- ' + item for item in data.get('what_i_liked', []))}

AREAS FOR IMPROVEMENT (according to user):
{chr(10).join('- ' + item for item in data.get('needs_improvement', []))}

USER'S OVERALL SCORE: {data.get('my_score', 'N/A')}/10
{scores_text}
Write an engaging, professional review that:
1. Opens with a hook that captures the game's essence
2. Expands on what makes the gameplay special based on user's likes
3. Discusses the game's strengths in detail (reference category scores if provided)
4. Acknowledges the areas that need improvement constructively
5. Concludes with who would enjoy this game

Write in a professional but passionate tone, like IGN or GameSpot.
Format with <p> tags for paragraphs. DO NOT use markdown."""
    
    return call_llm(prompt, data_table=None, config=config)


def generate_target_audience(
    data_points: List[Dict[str, Any]],
    stats: Dict[str, Any],
    config: "ReportConfig",
    _images_dir_rel: str = ""
) -> str:
    """
    Generate "Perfect for..." / "Who should play" section.
    """
    data = stats
    
    prompt = f"""Based on this game review, create a "Perfect For" section describing who would love this game.

GAME: {data.get('name', 'Unknown Game')}
GENRE: {data.get('genre', 'Unknown')}
WHAT'S GOOD: {', '.join(data.get('what_i_liked', []))}
SCORE: {data.get('my_score', 'N/A')}/10

Generate a brief section (2-3 bullet points) describing the ideal audience:
- Use phrases like "Perfect for fans of...", "Great for players who enjoy...", "Recommended if you..."
- Be specific based on the game's strengths

Format as an HTML unordered list (<ul><li>...</li></ul>). DO NOT use markdown."""
    
    return call_llm(prompt, data_table=None, config=config)


def generate_similar_games(
    data_points: List[Dict[str, Any]],
    stats: Dict[str, Any],
    config: "ReportConfig",
    _images_dir_rel: str = ""
) -> str:
    """
    Generate "If you liked this, try..." recommendations.
    """
    data = stats
    
    prompt = f"""Suggest 3-4 similar games for someone who enjoyed this game.

GAME: {data.get('name', 'Unknown Game')}
GENRE: {data.get('genre', 'Unknown')}
WHAT'S GREAT ABOUT IT: {', '.join(data.get('what_i_liked', []))}

For each recommendation:
- Name the game
- Briefly explain why it's similar (1 sentence)

Format as HTML: create cards using this structure:
<div class="rec-list">
<div class="rec-card"><strong>Game Name</strong><span>Brief reason for recommendation</span></div>
</div>

List 3-4 games. DO NOT use markdown. Use only the HTML structure above."""
    
    return call_llm(prompt, data_table=None, config=config)


def generate_expanded_pros(
    data_points: List[Dict[str, Any]],
    stats: Dict[str, Any],
    config: "ReportConfig",
    _images_dir_rel: str = ""
) -> str:
    """
    Expand user's brief likes into detailed pros.
    """
    data = stats
    user_likes = data.get('what_i_liked', [])
    
    if not user_likes:
        return ""
    
    prompt = f"""Expand these brief positive points about {data.get('name', 'a game')} into more detailed descriptions.

USER'S BRIEF LIKES:
{chr(10).join('- ' + item for item in user_likes)}

For each point, write 1-2 sentences expanding on why it's a strength.
Format as an HTML list: <ul><li><strong>Topic:</strong> Detailed explanation</li></ul>
DO NOT use markdown."""
    
    return call_llm(prompt, data_table=None, config=config)


def generate_expanded_cons(
    data_points: List[Dict[str, Any]],
    stats: Dict[str, Any],
    config: "ReportConfig",
    _images_dir_rel: str = ""
) -> str:
    """
    Expand user's brief improvements into constructive criticism.
    """
    data = stats
    user_improvements = data.get('needs_improvement', [])
    
    if not user_improvements:
        return "<p>No significant issues noted.</p>"
    
    prompt = f"""Expand these areas for improvement in {data.get('name', 'a game')} into constructive criticism.

AREAS FOR IMPROVEMENT:
{chr(10).join('- ' + item for item in user_improvements)}

For each point, write 1-2 sentences explaining the issue constructively (not harshly).
Format as an HTML list: <ul><li><strong>Topic:</strong> Constructive explanation</li></ul>
DO NOT use markdown."""
    
    return call_llm(prompt, data_table=None, config=config)


def generate_verdict(
    data_points: List[Dict[str, Any]],
    stats: Dict[str, Any],
    config: "ReportConfig",
    _images_dir_rel: str = ""
) -> str:
    """
    Generate a compelling final verdict.
    """
    data = stats
    score = data.get('my_score', 7)
    
    prompt = f"""Write a compelling 2-3 sentence final verdict for this game review.

GAME: {data.get('name', 'Unknown Game')}
SCORE: {score}/10
MAIN STRENGTHS: {', '.join(data.get('what_i_liked', [])[:3])}
MAIN WEAKNESSES: {', '.join(data.get('needs_improvement', [])[:2]) if data.get('needs_improvement') else 'Minor issues only'}

Write a memorable conclusion that:
- Captures the essence of the game in one impactful sentence
- Justifies the score briefly
- Ends with a recommendation statement

Format as a single paragraph. DO NOT use markdown or HTML tags."""
    
    return call_llm(prompt, data_table=None, config=config)
