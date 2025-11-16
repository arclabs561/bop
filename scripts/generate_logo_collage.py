#!/usr/bin/env python3
"""
Generate a 5x5 collage of logo/icon concepts for BOP repository.
Uses Gemini to generate concept prompts, then creates images.
"""

import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont
import io
import requests

# Load environment variables
load_dotenv()

# Project themes from README and ARCHITECTURE
BOP_THEMES = """
BOP (Knowledge Structure Research Agent) is about:
- Knowledge structure research and reasoning
- "Shape of ideas" - how knowledge organizes itself
- Information geometry, topological structure, causal inference
- D-separation, clique complexes, attractor basins
- MCP lazy evaluation, structured reasoning schemas
- Research agent for deep knowledge exploration
- Theoretical foundations: Fisher Information, Betti numbers, edge-of-chaos dynamics
"""


async def generate_logo_concepts():
    """Use Gemini to generate 25 diverse logo concept prompts."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment")
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-pro')
    
    prompt = f"""Generate 25 diverse logo/icon concept descriptions for "BOP" (Knowledge Structure Research Agent).

Project themes: {BOP_THEMES}

For each of the 25 concepts, provide:
- title: A creative name (2-5 words)
- description: Visual description (2-3 sentences)
- elements: Key visual elements (comma-separated)
- style: Style direction (one word or short phrase)

Explore different visual metaphors:
- Knowledge structures, networks, graphs
- Information geometry, topology, shapes
- Research, exploration, discovery
- Causal relationships, connections
- The "shape of ideas"

Be creative and diverse: geometric shapes, network diagrams, abstract forms, symbolic representations, mathematical visualizations, etc.

Output format: For each concept, write exactly:
Title: [name]
Description: [description]
Elements: [elements]
Style: [style]

Then a blank line before the next concept."""
    
    print("Generating logo concepts with Gemini...")
    response = model.generate_content(prompt)
    concepts_text = response.text
    
    # Save raw response for debugging
    with open('logo_concepts_raw.txt', 'w') as f:
        f.write(concepts_text)
    print("Raw response saved to logo_concepts_raw.txt")
    
    # Parse concepts - more flexible parsing
    concepts = []
    lines = concepts_text.split('\n')
    current_concept = {}
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines (but save concept if we have one)
        if not line:
            if current_concept and all(k in current_concept for k in ['title', 'description']):
                concepts.append(current_concept)
                current_concept = {}
            continue
        
        # Try different patterns
        if line.lower().startswith('title:'):
            if current_concept and all(k in current_concept for k in ['title', 'description']):
                concepts.append(current_concept)
            current_concept = {'title': line.split(':', 1)[1].strip()}
        elif line.lower().startswith('description:'):
            current_concept['description'] = line.split(':', 1)[1].strip()
        elif line.lower().startswith('elements:'):
            current_concept['elements'] = line.split(':', 1)[1].strip()
        elif line.lower().startswith('style:'):
            current_concept['style'] = line.split(':', 1)[1].strip()
        # Handle numbered lists
        elif line and line[0].isdigit() and ('.' in line or ')' in line or ':' in line):
            if current_concept and all(k in current_concept for k in ['title', 'description']):
                concepts.append(current_concept)
            # Extract title from numbered line
            title_part = line.split(':', 1)[-1].split('.', 1)[-1].strip()
            current_concept = {'title': title_part if title_part else f'Concept {len(concepts) + 1}'}
    
    # Add last concept
    if current_concept and all(k in current_concept for k in ['title', 'description']):
        concepts.append(current_concept)
    
    # Fill in missing fields
    for concept in concepts:
        if 'elements' not in concept:
            concept['elements'] = 'Geometric shapes, network connections'
        if 'style' not in concept:
            concept['style'] = 'Minimalist'
    
    # Ensure we have 25 concepts - generate more if needed
    base_concepts = [
        ('Interconnected Nodes', 'Network of connected nodes representing knowledge relationships', 'Nodes, edges, connections', 'Geometric'),
        ('Topological Surface', 'Curved surface with holes representing information topology', 'Surface, holes, curvature', 'Abstract'),
        ('Causal Graph', 'Directed graph showing causal relationships', 'Arrows, nodes, paths', 'Minimalist'),
        ('Attractor Basin', 'Visualization of attractor basins in knowledge space', 'Basins, flows, convergence', 'Abstract'),
        ('Clique Complex', 'Geometric representation of maximal cliques', 'Triangles, polygons, connections', 'Geometric'),
        ('Fisher Information', 'Matrix visualization of information geometry', 'Grid, matrix, structure', 'Technical'),
        ('D-Separation', 'Graph showing d-separation and conditional independence', 'Graph, paths, blocking', 'Minimalist'),
        ('Knowledge Lattice', 'Hierarchical lattice structure of knowledge', 'Lattice, hierarchy, levels', 'Geometric'),
        ('Information Flow', 'Flowing lines representing information streams', 'Flows, streams, paths', 'Abstract'),
        ('Research Compass', 'Compass pointing to knowledge discovery', 'Compass, direction, exploration', 'Symbolic'),
    ]
    
    while len(concepts) < 25:
        idx = len(concepts) % len(base_concepts)
        title, desc, elements, style = base_concepts[idx]
        concepts.append({
            'title': f'{title} Variant {len(concepts) // len(base_concepts) + 1}',
            'description': desc,
            'elements': elements,
            'style': style
        })
    
    return concepts[:25]


def wrap_text(text, max_width, font, draw):
    """Wrap text to fit within max_width."""
    words = text.split()
    lines = []
    current_line = []
    current_width = 0
    
    for word in words:
        word_width = draw.textlength(word + ' ', font=font)
        if current_width + word_width <= max_width:
            current_line.append(word)
            current_width += word_width
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
            current_width = word_width
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines


def create_image_placeholder(concept, index, size=(400, 400)):
    """Create a placeholder image with concept description."""
    img = Image.new('RGB', size, color='#f8f9fa')
    draw = ImageDraw.Draw(img)
    
    # Try to use a nice font
    try:
        font_title = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
        font_desc = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 11)
        font_meta = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 10)
    except:
        try:
            font_title = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 20)
            font_desc = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 11)
            font_meta = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 10)
        except:
            font_title = ImageFont.load_default()
            font_desc = ImageFont.load_default()
            font_meta = ImageFont.load_default()
    
    # Draw border with subtle color
    border_color = '#4a90e2' if index % 2 == 0 else '#50c878'
    draw.rectangle([5, 5, size[0]-5, size[1]-5], outline=border_color, width=3)
    
    # Number badge in corner
    badge_center = (size[0]-27, 27)
    draw.ellipse([size[0]-45, 10, size[0]-10, 45], fill='#333', outline='#fff', width=2)
    # Center text in badge manually
    text_bbox = draw.textbbox((0, 0), str(index + 1), font=font_title)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    draw.text((badge_center[0] - text_width/2, badge_center[1] - text_height/2), 
              str(index + 1), fill='#fff', font=font_title)
    
    # Title
    title = concept.get('title', f'Concept {index + 1}')
    title_lines = wrap_text(title, size[0] - 40, font_title, draw)
    y = 15
    for line in title_lines[:2]:  # Max 2 lines
        draw.text((15, y), line, fill='#1a1a1a', font=font_title)
        y += 28
    
    # Description
    desc = concept.get('description', '')
    if desc:
        desc_lines = wrap_text(desc, size[0] - 30, font_desc, draw)
        y += 5
        for line in desc_lines[:4]:  # Max 4 lines
            draw.text((15, y), line, fill='#444', font=font_desc)
            y += 16
    
    # Elements
    elements = concept.get('elements', '')
    if elements and y < size[1] - 50:
        draw.text((15, y + 5), "Elements:", fill='#666', font=font_meta)
        elem_lines = wrap_text(elements, size[0] - 30, font_meta, draw)
        y += 18
        for line in elem_lines[:2]:  # Max 2 lines
            draw.text((15, y), line, fill='#777', font=font_meta)
            y += 14
    
    # Style at bottom
    style = concept.get('style', '')
    if style:
        draw.text((15, size[1] - 25), f"Style: {style}", fill='#999', font=font_meta)
    
    return img


def create_collage(concepts, output_path='logo_concepts_collage.png'):
    """Create a 5x5 collage of concept images."""
    cell_size = 400
    grid_size = 5
    collage_size = (cell_size * grid_size, cell_size * grid_size)
    
    collage = Image.new('RGB', collage_size, color='white')
    
    print(f"Creating {grid_size}x{grid_size} collage...")
    for i, concept in enumerate(concepts):
        row = i // grid_size
        col = i % grid_size
        
        # Create placeholder image
        img = create_image_placeholder(concept, i, (cell_size, cell_size))
        
        # Paste into collage
        x = col * cell_size
        y = row * cell_size
        collage.paste(img, (x, y))
        
        print(f"  Added concept {i+1}/25: {concept.get('title', 'Untitled')}")
    
    collage.save(output_path)
    print(f"\nCollage saved to: {output_path}")
    return output_path


async def main():
    """Main function to generate concepts and create collage."""
    print("BOP Logo Concept Generator")
    print("=" * 50)
    
    # Generate concepts
    concepts = await generate_logo_concepts()
    
    # Save concepts to file
    concepts_file = Path('logo_concepts.txt')
    with open(concepts_file, 'w') as f:
        for i, concept in enumerate(concepts, 1):
            f.write(f"\n{'='*60}\n")
            f.write(f"Concept {i}: {concept.get('title', 'Untitled')}\n")
            f.write(f"{'='*60}\n")
            f.write(f"Description: {concept.get('description', 'N/A')}\n")
            f.write(f"Elements: {concept.get('elements', 'N/A')}\n")
            f.write(f"Style: {concept.get('style', 'N/A')}\n")
    print(f"\nConcepts saved to: {concepts_file}")
    
    # Create collage
    output_path = Path('logo_concepts_collage.png')
    create_collage(concepts, str(output_path))
    
    print("\n" + "=" * 50)
    print("Next steps:")
    print("1. Review the collage and concepts file")
    print("2. Comment on which concepts you like")
    print("3. We can iterate and generate actual logo images for selected concepts")


if __name__ == '__main__':
    asyncio.run(main())

