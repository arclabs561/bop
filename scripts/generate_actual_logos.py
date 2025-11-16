#!/usr/bin/env python3
"""
Generate actual logo images for BOP concepts using image generation APIs.
"""

import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image
from io import BytesIO
import requests

# Try to import google-genai (new SDK)
try:
    from google import genai
    from google.genai import types
    GOOGLE_GENAI_AVAILABLE = True
except ImportError:
    GOOGLE_GENAI_AVAILABLE = False
    print("Warning: google-genai not available, install with: uv add google-genai")

load_dotenv()


def load_concepts():
    """Load concepts from the generated file."""
    concepts = []
    with open('logo_concepts.txt', 'r') as f:
        content = f.read()
    
    # Parse concepts - split by separator lines
    sections = content.split('=' * 60)
    
    for section in sections[1:]:  # Skip first empty section
        lines = [l.strip() for l in section.strip().split('\n') if l.strip()]
        if not lines:
            continue
        
        concept = {}
        for line in lines:
            if line.startswith('Concept') and ':' in line:
                # Extract concept number and title
                parts = line.split(':', 1)
                if len(parts) > 1:
                    concept['title'] = parts[1].strip()
            elif line.startswith('Description:'):
                concept['description'] = line.split(':', 1)[1].strip()
            elif line.startswith('Elements:'):
                concept['elements'] = line.split(':', 1)[1].strip()
            elif line.startswith('Style:'):
                concept['style'] = line.split(':', 1)[1].strip()
        
        if concept.get('title') and concept.get('description'):
            concepts.append(concept)
    
    # If parsing failed, try alternative approach
    if len(concepts) < 10:
        # Re-read and try different parsing
        with open('logo_concepts.txt', 'r') as f:
            lines = f.readlines()
        
        concept = {}
        for line in lines:
            line = line.strip()
            if not line or line.startswith('='):
                if concept.get('title') and concept.get('description'):
                    concepts.append(concept)
                    concept = {}
                continue
            
            if 'Concept' in line and ':' in line:
                parts = line.split(':', 1)
                if len(parts) > 1:
                    concept['title'] = parts[1].strip()
            elif line.startswith('Description:'):
                concept['description'] = line.split(':', 1)[1].strip()
            elif line.startswith('Elements:'):
                concept['elements'] = line.split(':', 1)[1].strip()
            elif line.startswith('Style:'):
                concept['style'] = line.split(':', 1)[1].strip()
        
        if concept.get('title') and concept.get('description'):
            concepts.append(concept)
    
    return concepts[:25]  # Ensure exactly 25


def generate_image_gemini(concept, index):
    """Generate image using Gemini Imagen API (2025 - latest SDK)."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("  No Gemini API key found")
        return None
    
    if not GOOGLE_GENAI_AVAILABLE:
        print("  google-genai SDK not available")
        return None
    
    try:
        print("  Using Gemini Imagen 4.0 for image generation...")
        
        prompt = f"""Create a vibrant, colorful logo icon design for "{concept.get('title', 'Logo')}".

Visual description: {concept.get('description', 'Abstract geometric logo')}
Key elements to include: {concept.get('elements', 'Geometric shapes')}
Style: {concept.get('style', 'Modern')}

Requirements:
- Bold, colorful design with vibrant colors (use rich blues, purples, greens, oranges, gradients)
- Geometric, abstract logo suitable for use as an icon
- Clean, professional but visually striking
- Use gradients, color transitions, and modern color palettes
- No text, just the visual symbol
- Recognizable at small sizes (icon-friendly)
- Modern, dynamic aesthetic with depth and visual interest
- Similar style to architectural/geometric designs with interlocking shapes and depth"""

        # Initialize client with API key
        print("  Initializing Gemini client...")
        client = genai.Client(api_key=api_key)
        
        # Generate image using Imagen 4.0
        print("  Sending request to Imagen 4.0...")
        response = client.models.generate_images(
            model='imagen-4.0-generate-001',  # Latest Imagen model
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio='1:1',  # Square for logos
            )
        )
        
        print("  Response received, extracting image...")
        
        # Extract image from response
        if response.generated_images and len(response.generated_images) > 0:
            generated_image = response.generated_images[0]
            img_bytes = generated_image.image.image_bytes
            
            print("  Converting to PIL Image...")
            img = Image.open(BytesIO(img_bytes))
            print("  ✓ Image generated successfully")
            return img
        else:
            print("  No images in response")
            return None
            
    except Exception as e:
        print(f"  Gemini image generation failed: {type(e).__name__}: {e}")
        import traceback
        print(f"  Traceback: {traceback.format_exc()[:300]}")
        return None


def generate_image_openai(concept, index):
    """Generate image using OpenAI DALL-E."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("  No OpenAI API key found, skipping...")
        return None
    
    try:
        print("  Trying OpenAI DALL-E...")
        prompt = f"""Minimalist logo icon design: {concept['title']}. {concept['description']}. 
Key elements: {concept['elements']}. Style: {concept['style']}. 
Simple, geometric, abstract logo suitable for use as an icon. Black and white or minimal colors. 
No text, just the visual symbol."""
        
        print("  Sending request to OpenAI...")
        response = requests.post(
            "https://api.openai.com/v1/images/generations",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "dall-e-3",
                "prompt": prompt,
                "n": 1,
                "size": "1024x1024",
                "quality": "standard",
                "style": "natural"
            },
            timeout=60
        )
        
        print(f"  Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            image_url = data['data'][0]['url']
            print(f"  Image URL received, downloading...")
            
            # Download image
            img_response = requests.get(image_url, timeout=30)
            if img_response.status_code == 200:
                print("  Image downloaded successfully")
                return Image.open(requests.get(image_url, stream=True).raw)
            else:
                print(f"  Download failed: {img_response.status_code}")
        else:
            print(f"  OpenAI API error: {response.status_code} - {response.text[:200]}")
            return None
    except requests.Timeout:
        print("  OpenAI request timed out")
        return None
    except Exception as e:
        print(f"  OpenAI image generation failed: {e}")
        return None


def generate_image_fallback(concept, index):
    """Create a simple geometric representation as fallback."""
    from PIL import ImageDraw
    import math
    
    print("  Creating geometric fallback design...")
    img = Image.new('RGB', (1024, 1024), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw a simple geometric pattern based on concept
    center = (512, 512)
    
    # Different patterns based on concept title
    title_lower = concept.get('title', '').lower()
    
    if 'node' in title_lower or 'network' in title_lower or 'connected' in title_lower:
        # Draw nodes and connections
        nodes = [
            (300, 300), (724, 300), (512, 512),
            (300, 724), (724, 724)
        ]
        for node in nodes:
            draw.ellipse([node[0]-40, node[1]-40, node[0]+40, node[1]+40], 
                        fill='#333', outline='#000', width=3)
        for i in range(len(nodes)):
            for j in range(i+1, len(nodes)):
                draw.line([nodes[i], nodes[j]], fill='#666', width=2)
    
    elif 'arrow' in title_lower or 'causal' in title_lower:
        # Draw arrow
        draw.polygon([(200, 512), (700, 300), (700, 400), 
                      (800, 400), (800, 624), (700, 624), (700, 724)],
                    fill='#333', outline='#000', width=3)
    
    elif 'torus' in title_lower or 'topological' in title_lower:
        # Draw torus-like shape
        for i in range(0, 360, 20):
            import math
            angle = math.radians(i)
            x1 = center[0] + 200 * math.cos(angle)
            y1 = center[1] + 200 * math.sin(angle)
            x2 = center[0] + 300 * math.cos(angle)
            y2 = center[1] + 300 * math.sin(angle)
            draw.ellipse([x1-30, y1-30, x1+30, y1+30], 
                        fill='#333', outline='#000', width=2)
            draw.line([(x1, y1), (x2, y2)], fill='#666', width=2)
    
    elif 'lens' in title_lower or 'structural' in title_lower:
        # Draw lens/magnifying glass
        draw.ellipse([300, 300, 724, 724], outline='#333', width=5)
        draw.line([(724, 512), (850, 650)], fill='#333', width=5)
        # Inner pattern
        for i in range(5):
            x = 400 + i * 60
            y = 400 + i * 60
            draw.ellipse([x-20, y-20, x+20, y+20], fill='#666')
    
    elif 'compass' in title_lower or 'beacon' in title_lower:
        # Draw compass
        draw.ellipse([300, 300, 724, 724], outline='#333', width=5)
        draw.line([(512, 300), (512, 724)], fill='#333', width=3)
        draw.line([(300, 512), (724, 512)], fill='#333', width=3)
        draw.polygon([(512, 300), (500, 350), (524, 350)], fill='#333')
    
    else:
        # Default: abstract geometric shape - hexagon
        import math
        def draw_polygon(center, radius, sides, fill=None, outline=None, width=1):
            points = []
            for i in range(sides):
                angle = 2 * math.pi * i / sides - math.pi / 2
                x = center[0] + radius * math.cos(angle)
                y = center[1] + radius * math.sin(angle)
                points.append((x, y))
            if fill:
                draw.polygon(points, fill=fill, outline=outline, width=width)
            else:
                draw.polygon(points, outline=outline, width=width)
        
        draw_polygon(center, 200, 6, fill='#333', outline='#000', width=3)
        # Add inner pattern
        for i in range(3):
            size = 150 - i * 30
            draw_polygon(center, size, 6, outline='#666', width=2)
    
    return img


def generate_all_logos(concepts):
    """Generate images for all concepts."""
    output_dir = Path('logo_images')
    output_dir.mkdir(exist_ok=True)
    
    print(f"Generating {len(concepts)} logo images...")
    print("=" * 60)
    print(f"Output directory: {output_dir.absolute()}")
    print()
    
    generated = []
    start_time = time.time()
    
    for i, concept in enumerate(concepts, 1):
        elapsed = time.time() - start_time
        print(f"\n[{i}/25] {concept.get('title', 'Untitled')} (elapsed: {elapsed:.1f}s)")
        print(f"  Description: {concept.get('description', '')[:60]}...")
        
        img = None
        
        # Try Gemini first (prioritized for images)
        if os.getenv("GEMINI_API_KEY"):
            img = generate_image_gemini(concept, i)
        
        if img is None:
            # Fallback to OpenAI DALL-E
            if os.getenv("OPENAI_API_KEY"):
                img = generate_image_openai(concept, i)
        
        if img is None:
            # Fallback to simple geometric
            print("  Using fallback geometric design...")
            img = generate_image_fallback(concept, i)
        
        if img:
            # Resize to larger size for better quality
            print("  Resizing image to 1024x1024...")
            img = img.resize((1024, 1024), Image.Resampling.LANCZOS)
            
            # Save
            safe_title = concept.get('title', 'untitled').replace(' ', '_').replace('/', '_').lower()[:30]
            output_path = output_dir / f"logo_{i:02d}_{safe_title}.png"
            print(f"  Saving to {output_path.name}...")
            img.save(output_path)
            generated.append((i, output_path, concept))
            print(f"  ✓ Saved: {output_path}")
        else:
            print(f"  ✗ Failed to generate image")
        
        # Progress summary
        progress = (i / len(concepts)) * 100
        print(f"  Progress: {progress:.1f}% ({i}/{len(concepts)})")
        
        # Rate limiting (only for API calls, not fallback)
        if img and i < len(concepts):
            print("  Waiting 1s before next generation...")
            time.sleep(1)
    
    total_time = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"Total time: {total_time:.1f}s")
    print(f"Average per image: {total_time/len(concepts):.1f}s")
    
    return generated


def create_collage_from_images(generated_images, output_path='logo_collage_actual.png'):
    """Create 5x5 collage from generated images."""
    cell_size = 1024  # Larger cells for better detail
    grid_size = 5
    collage_size = (cell_size * grid_size, cell_size * grid_size)
    
    collage = Image.new('RGB', collage_size, color='white')
    
    print(f"\nCreating collage from {len(generated_images)} images...")
    
    for i, (num, img_path, concept) in enumerate(generated_images):
        try:
            img = Image.open(img_path)
            # Keep original size if already 1024x1024, otherwise resize
            if img.size[0] != cell_size or img.size[1] != cell_size:
                img = img.resize((cell_size, cell_size), Image.Resampling.LANCZOS)
            
            row = (num - 1) // grid_size
            col = (num - 1) % grid_size
            
            x = col * cell_size
            y = row * cell_size
            collage.paste(img, (x, y))
            
            print(f"  Added {num}/25: {concept.get('title', 'Untitled')}")
        except Exception as e:
            print(f"  Error loading {img_path}: {e}")
    
    collage.save(output_path)
    print(f"\n✓ Collage saved to: {output_path}")
    return output_path


def main():
    """Main function."""
    print("BOP Logo Image Generator")
    print("=" * 60)
    
    # Load concepts
    concepts = load_concepts()
    print(f"Loaded {len(concepts)} concepts")
    
    # Generate images
    generated = generate_all_logos(concepts)
    
    # Create collage
    if generated:
        create_collage_from_images(generated)
        print(f"\n✓ Generated {len(generated)} logo images")
        print(f"  Images saved in: logo_images/")
    else:
        print("\n✗ No images were generated")


if __name__ == '__main__':
    main()

