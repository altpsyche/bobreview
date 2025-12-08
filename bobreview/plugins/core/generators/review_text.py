"""
Generate game review text using LLM.

Creates a professional game review based on scores, pros, cons, and game details.
"""

from typing import Dict, List, Any, Optional


def generate_review_text(
    data_points: List[Dict[str, Any]],
    stats: Dict[str, Any],
    config: Any,
    images_dir: str = ""
) -> str:
    """
    Generate a professional game review using LLM.
    
    This function follows the universal generator signature that works
    with the LLMGeneratorAdapter:
    - data_points: Raw data points (unused for game reviews)
    - stats: Parsed data - for game reviews, this IS the game data
    - config: Report configuration
    - images_dir: Images directory (unused for game reviews)
    
    For game reviews, `stats` contains the game info from game.json:
    - title, developer, genre, scores, pros, cons, etc.
    
    Returns:
        Generated review HTML text
    """
    # For game reviews, stats IS the game data
    # The GameConfigParser returns the game dict as stats
    data = stats
    
    # Get LLM client from config if available
    llm_client = None
    if hasattr(config, 'llm_client'):
        llm_client = config.llm_client
    
    if llm_client is None:
        # When there's no LLM client, return empty (LLM will be called separately)
        # The prompt is returned for template-based generation
        pass
    
    # Calculate overall score
    scores = data.get('scores', {})
    if not scores:
        return ""
    
    overall = (
        scores.get('gameplay', 5) +
        scores.get('graphics', 5) +
        scores.get('story', 5) +
        scores.get('sound', 5) +
        scores.get('value', 5)
    ) / 5
    
    # Build prompt
    prompt = f"""Write a professional video game review for the following game.

GAME INFORMATION:
- Title: {data.get('title', 'Unknown')}
- Developer: {data.get('developer', 'Unknown')}
- Publisher: {data.get('publisher', 'Unknown')}
- Genre: {data.get('genre', 'Unknown')}
- Release Date: {data.get('release_date', 'Unknown')}

SCORES (out of 10):
- Gameplay: {scores.get('gameplay', 'N/A')}
- Graphics: {scores.get('graphics', 'N/A')}
- Story: {scores.get('story', 'N/A')}
- Sound: {scores.get('sound', 'N/A')}
- Value: {scores.get('value', 'N/A')}
- Overall: {overall:.1f}/10

PROS:
{chr(10).join('- ' + pro for pro in data.get('pros', []))}

CONS:
{chr(10).join('- ' + con for con in data.get('cons', []))}

SUMMARY PROVIDED:
{data.get('summary', 'No summary provided.')}

Write a 3-4 paragraph professional game review that:
1. Opens with an engaging introduction about the game
2. Discusses the gameplay and what makes it special (or not)
3. Covers graphics, sound, and presentation
4. Concludes with who this game is for and final thoughts

Write in a professional but engaging tone, similar to IGN or GameSpot reviews.
Format the response with <p> tags for paragraphs.
"""
    
    # Return the prompt - the LLM service will call the API
    # For Python generators, we return the generated content
    # In this case, we'd need the LLM to be called externally
    
    # If there's a direct LLM client, use it
    if llm_client and callable(getattr(llm_client, 'call', None)):
        try:
            response = llm_client.call(prompt)
            return response if response else ""
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to generate review text: {e}")
            return ""
    
    # Otherwise return the prompt for template-based generation
    # The executor will handle the LLM call
    return prompt
