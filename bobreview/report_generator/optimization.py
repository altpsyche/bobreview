#!/usr/bin/env python3
"""
Optimization checklist page generator with actionable recommendations.
"""

from html import escape
from typing import Dict, List, Any
from .base import get_html_template, get_page_header, get_image_src, sanitize_llm_html
from ..utils import format_number


def generate_optimization_page(
    data_points: List[Dict[str, Any]], 
    stats: Dict[str, Any], 
    images_dir_rel: str,
    image_data_uris: Dict[str, str],
    config,
    optimization_content: Dict[str, str],
    system_recs: Dict[str, str]
) -> str:
    """
    Generate the optimization checklist page with recommendations.
    
    Parameters:
        data_points: List of parsed capture records
        stats: Aggregated analysis results
        images_dir_rel: Relative path to images directory
        image_data_uris: Mapping of image names to base64 data URIs
        config: Report configuration
        optimization_content: Optimization recommendations from LLM
        system_recs: System-level recommendations from LLM
    
    Returns:
        Complete HTML document for the optimization page
    """
    nav_items = [
        ("Home", "index.html", False),
        ("Metrics", "metrics.html", False),
        ("Zones & Hotspots", "zones.html", False),
        ("Visual Analysis", "visuals.html", False),
        ("Optimization", "optimization.html", True),
        ("Statistics", "stats.html", False),
    ]
    
    header = get_page_header("Optimization Checklist", f"{stats['count']} captures · {config.location}", nav_items)
    
    critical_idx = stats['critical'][0]
    critical_point = stats['critical'][1]
    critical_draws = critical_point['draws']
    critical_tris = format_number(critical_point['tris'])
    critical_img = critical_point['img']
    
    # Count high-geometry and high-draw hotspots
    high_geometry_count = len([p for _, p in stats['high_load'] if p['tris'] >= config.high_load_tri_threshold])
    high_draw_count = len([p for _, p in stats['high_load'] if p['draws'] >= config.high_load_draw_threshold])
    
    # System recommendations section
    system_recs_section = ""
    if config.enable_recommendations and system_recs.get('full'):
        system_recs_section = f"""
    <section class="panel" style="margin-top: 20px;">
      <h2>System-Level Recommendations</h2>
      <p class="body-text">
        Strategic recommendations for improving overall performance architecture and workflow.
      </p>
      {sanitize_llm_html(system_recs['full'])}
    </section>
"""
    
    body_content = f"""{header}
    
    <section class="panel">
      <h2>Performance Budgets</h2>
      <p class="body-text">
        Establish and maintain performance budgets to ensure consistent frame rates and responsive gameplay.
        Any capture exceeding the hard cap should be treated as a performance issue.
      </p>
      
      <div class="summary-grid">
        <div class="stat-card ok">
          <div class="stat-label">Draw Calls Budget</div>
          <div class="stat-value">&le; {config.draw_soft_cap}</div>
          <div class="stat-sub">Soft cap {config.draw_soft_cap} &middot; hard cap {config.draw_hard_cap}</div>
        </div>
        
        <div class="stat-card ok">
          <div class="stat-label">Triangle Budget</div>
          <div class="stat-value">&le; {format_number(config.tri_soft_cap / 1000, 0)}k</div>
          <div class="stat-sub">Soft cap {format_number(config.tri_soft_cap, 0)} &middot; hard cap {format_number(config.tri_hard_cap, 0)}</div>
        </div>
        
        <div class="stat-card warn">
          <div class="stat-label">Current Status</div>
          <div class="stat-value">{len([p for p in data_points if p['draws'] > config.draw_hard_cap or p['tris'] > config.tri_hard_cap])}</div>
          <div class="stat-sub">Frames exceeding hard caps</div>
        </div>
      </div>
      
      <div class="callout warn" style="margin-top: 16px;">
        <div class="callout-title">Budget Guidelines</div>
        <ul class="body-text">
          <li><strong>Soft Cap:</strong> Target performance level for most scenes. Aim to stay below this threshold.</li>
          <li><strong>Hard Cap:</strong> Maximum acceptable performance cost. Exceeding this requires immediate optimization.</li>
          <li><strong>Budget Tracking:</strong> Monitor budgets across all development stages to prevent performance regressions.</li>
        </ul>
      </div>
    </section>
    
    <section class="panel" style="margin-top: 20px;">
      <h2>Critical Hotspot - Index {critical_idx}</h2>
      <p class="body-text">
        The highest-priority optimization target. This frame has the worst performance characteristics 
        and should be addressed first for maximum impact.
      </p>
      
      <div class="callout critical">
        <div class="callout-title">Index {critical_idx} – {escape(critical_img)}</div>
        <div><strong>{critical_draws} draw calls</strong> &middot; <strong>{critical_tris} triangles</strong></div>
        <div style="margin-top: 8px; font-size: 12px;">
          Exceeds draw budget by: {max(0, critical_draws - config.draw_hard_cap)} calls
          {' | ' if critical_point['tris'] > config.tri_hard_cap else ''}
          {'Exceeds tri budget by: ' + format_number(critical_point['tris'] - config.tri_hard_cap) + ' tris' if critical_point['tris'] > config.tri_hard_cap else ''}
        </div>
      </div>
      
      <img
        class="thumb-large"
        src="{get_image_src(critical_img, images_dir_rel, image_data_uris)}"
        alt="Critical hotspot frame (index {critical_idx})"
        style="max-width: 100%; margin-top: 12px;"
      />
      
      {sanitize_llm_html(optimization_content.get('critical', ''))}
      
      <div class="callout" style="margin-top: 12px;">
        <div class="callout-title">Recommended Actions</div>
        <ul class="body-text">
          <li>Profile this specific frame to identify expensive draw calls</li>
          <li>Look for redundant or unnecessary rendering operations</li>
          <li>Consider LOD (Level of Detail) systems for distant objects</li>
          <li>Investigate potential for object culling or occlusion</li>
          <li>Batch similar materials and meshes where possible</li>
        </ul>
      </div>
    </section>
    
    <section class="panel" style="margin-top: 20px;">
      <h2>High-Geometry Hotspots</h2>
      <p class="body-text">
        Frames with excessive triangle counts (≥ {format_number(config.high_load_tri_threshold, 0)} triangles).
        Affects <strong>{high_geometry_count} frame(s)</strong>.
      </p>
      
      {sanitize_llm_html(optimization_content.get('high_geometry', ''))}
      
      <div class="callout" style="margin-top: 12px;">
        <div class="callout-title">Geometry Optimization Strategies</div>
        <ul class="body-text">
          <li><strong>LOD Systems:</strong> Implement multiple levels of detail for complex meshes</li>
          <li><strong>Mesh Simplification:</strong> Reduce polygon counts on distant or less important objects</li>
          <li><strong>Frustum Culling:</strong> Ensure objects outside the camera view are not rendered</li>
          <li><strong>Occlusion Culling:</strong> Skip rendering objects hidden behind other geometry</li>
          <li><strong>Instancing:</strong> Use GPU instancing for repeated geometry</li>
        </ul>
      </div>
    </section>
    
    <section class="panel" style="margin-top: 20px;">
      <h2>High-Draw Hotspots</h2>
      <p class="body-text">
        Frames with excessive draw calls (≥ {config.high_load_draw_threshold} draws).
        Affects <strong>{high_draw_count} frame(s)</strong>.
      </p>
      
      {sanitize_llm_html(optimization_content.get('high_draw', ''))}
      
      <div class="callout" style="margin-top: 12px;">
        <div class="callout-title">Draw Call Optimization Strategies</div>
        <ul class="body-text">
          <li><strong>Batching:</strong> Combine meshes with identical materials into single draw calls</li>
          <li><strong>Material Reduction:</strong> Minimize unique material instances and shader variants</li>
          <li><strong>Atlasing:</strong> Combine multiple textures into texture atlases</li>
          <li><strong>GPU Instancing:</strong> Render multiple copies of the same mesh in one call</li>
          <li><strong>Static Batching:</strong> Pre-combine static geometry at build time</li>
          <li><strong>Dynamic Batching:</strong> Combine small dynamic objects at runtime</li>
        </ul>
      </div>
    </section>
    
{system_recs_section}
    
    <section class="panel" style="margin-top: 20px;">
      <h2>Optimization Priority Matrix</h2>
      <p class="body-text">
        Prioritize optimization work based on impact and effort. Focus on high-impact, low-effort improvements first.
      </p>
      
      <div class="stats-grid">
        <div class="stats-item" style="border-left: 3px solid var(--danger);">
          <div class="stats-item-label">Priority 1: Critical</div>
          <div class="stats-item-value">{len([p for p in data_points if (p['draws'] > config.draw_hard_cap * 1.2 or p['tris'] > config.tri_hard_cap * 1.2)])}</div>
        </div>
        
        <div class="stats-item" style="border-left: 3px solid var(--warn);">
          <div class="stats-item-label">Priority 2: High</div>
          <div class="stats-item-value">{len([p for p in data_points if (config.draw_hard_cap < p['draws'] <= config.draw_hard_cap * 1.2 or config.tri_hard_cap < p['tris'] <= config.tri_hard_cap * 1.2)])}</div>
        </div>
        
        <div class="stats-item" style="border-left: 3px solid var(--accent);">
          <div class="stats-item-label">Priority 3: Medium</div>
          <div class="stats-item-value">{len([p for p in data_points if (config.draw_soft_cap < p['draws'] <= config.draw_hard_cap or config.tri_soft_cap < p['tris'] <= config.tri_hard_cap)])}</div>
        </div>
        
        <div class="stats-item" style="border-left: 3px solid var(--ok);">
          <div class="stats-item-label">Within Budget</div>
          <div class="stats-item-value">{len([p for p in data_points if p['draws'] <= config.draw_soft_cap and p['tris'] <= config.tri_soft_cap])}</div>
        </div>
      </div>
    </section>
    
    <div class="footer">
      Generated by BobReview - <a href="index.html">Back to Home</a>
    </div>
"""
    
    return get_html_template(f"{config.title} - Optimization", body_content, include_chartjs=False)

