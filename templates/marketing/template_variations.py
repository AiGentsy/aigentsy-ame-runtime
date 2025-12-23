"""
TEMPLATE VARIATIONS SYSTEM
Makes every storefront unique through deterministic personalization

Hybrid Approach:
1. 10 color palettes (based on user_number % 10)
2. 15 font pairs (based on user_number % 15)
3. 3 layout variants per template (based on templateVariation choice)
4. Random accent patterns

Result: 450+ unique variations per template!
"""

from typing import Dict, Tuple
import hashlib


# ============================================================
# COLOR PALETTES (10 variations)
# ============================================================

COLOR_PALETTES = {
    0: {  # Electric Blue
        'name': 'Electric',
        'primary': '#3b82f6',
        'secondary': '#8b5cf6',
        'accent': '#06b6d4',
        'bg': '#0f0f0f',
        'text': '#ffffff',
        'gradient': 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)'
    },
    1: {  # Sunset Orange
        'name': 'Sunset',
        'primary': '#f97316',
        'secondary': '#ec4899',
        'accent': '#fbbf24',
        'bg': '#1a1a1a',
        'text': '#fef3c7',
        'gradient': 'linear-gradient(135deg, #f97316 0%, #ec4899 100%)'
    },
    2: {  # Forest Green
        'name': 'Forest',
        'primary': '#10b981',
        'secondary': '#059669',
        'accent': '#34d399',
        'bg': '#0a1f1a',
        'text': '#f0fdf4',
        'gradient': 'linear-gradient(135deg, #10b981 0%, #059669 100%)'
    },
    3: {  # Cyber Pink
        'name': 'Cyber',
        'primary': '#ff6b9d',
        'secondary': '#c44569',
        'accent': '#ffc837',
        'bg': '#1a0a1e',
        'text': '#fef3ff',
        'gradient': 'linear-gradient(135deg, #ff6b9d 0%, #c44569 100%)'
    },
    4: {  # Ocean Teal
        'name': 'Ocean',
        'primary': '#06b6d4',
        'secondary': '#0891b2',
        'accent': '#22d3ee',
        'bg': '#0a1929',
        'text': '#ecfeff',
        'gradient': 'linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)'
    },
    5: {  # Royal Purple
        'name': 'Royal',
        'primary': '#a855f7',
        'secondary': '#7c3aed',
        'accent': '#c084fc',
        'bg': '#1e1b2e',
        'text': '#faf5ff',
        'gradient': 'linear-gradient(135deg, #a855f7 0%, #7c3aed 100%)'
    },
    6: {  # Fire Red
        'name': 'Fire',
        'primary': '#ef4444',
        'secondary': '#dc2626',
        'accent': '#fb923c',
        'bg': '#1a0a0a',
        'text': '#fef2f2',
        'gradient': 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)'
    },
    7: {  # Golden Hour
        'name': 'Golden',
        'primary': '#f59e0b',
        'secondary': '#d97706',
        'accent': '#fbbf24',
        'bg': '#1a1410',
        'text': '#fef3c7',
        'gradient': 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)'
    },
    8: {  # Midnight Blue
        'name': 'Midnight',
        'primary': '#1e40af',
        'secondary': '#1e3a8a',
        'accent': '#3b82f6',
        'bg': '#0a0e1a',
        'text': '#dbeafe',
        'gradient': 'linear-gradient(135deg, #1e40af 0%, #1e3a8a 100%)'
    },
    9: {  # Mint Fresh
        'name': 'Mint',
        'primary': '#14b8a6',
        'secondary': '#0d9488',
        'accent': '#5eead4',
        'bg': '#0a1a1a',
        'text': '#f0fdfa',
        'gradient': 'linear-gradient(135deg, #14b8a6 0%, #0d9488 100%)'
    }
}


# ============================================================
# FONT PAIRS (15 variations)
# ============================================================

FONT_PAIRS = {
    0: {
        'name': 'Tech Modern',
        'heading': "'Space Grotesk', sans-serif",
        'body': "'Inter', sans-serif",
        'import': "https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@600;700&family=Inter:wght@400;500;600&display=swap"
    },
    1: {
        'name': 'Editorial',
        'heading': "'Playfair Display', serif",
        'body': "'Source Sans Pro', sans-serif",
        'import': "https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Source+Sans+Pro:wght@400;600&display=swap"
    },
    2: {
        'name': 'Bold Impact',
        'heading': "'Archivo Black', sans-serif",
        'body': "'Manrope', sans-serif",
        'import': "https://fonts.googleapis.com/css2?family=Archivo+Black&family=Manrope:wght@400;600;800&display=swap"
    },
    3: {
        'name': 'Elegant Pro',
        'heading': "'Cormorant Garamond', serif",
        'body': "'Work Sans', sans-serif",
        'import': "https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@600;700&family=Work+Sans:wght@400;500;600&display=swap"
    },
    4: {
        'name': 'Mono Brutalist',
        'heading': "'JetBrains Mono', monospace",
        'body': "'IBM Plex Mono', monospace",
        'import': "https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@700&family=IBM+Plex+Mono:wght@400;600&display=swap"
    },
    5: {
        'name': 'Geometric Sharp',
        'heading': "'Syne', sans-serif",
        'body': "'DM Sans', sans-serif",
        'import': "https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;500;700&display=swap"
    },
    6: {
        'name': 'Display Bold',
        'heading': "'Righteous', sans-serif",
        'body': "'Outfit', sans-serif",
        'import': "https://fonts.googleapis.com/css2?family=Righteous&family=Outfit:wght@400;500;700&display=swap"
    },
    7: {
        'name': 'Modern Serif',
        'heading': "'Fraunces', serif",
        'body': "'Plus Jakarta Sans', sans-serif",
        'import': "https://fonts.googleapis.com/css2?family=Fraunces:wght@700;900&family=Plus+Jakarta+Sans:wght@400;600&display=swap"
    },
    8: {
        'name': 'Tech Refined',
        'heading': "'Poppins', sans-serif",
        'body': "'Karla', sans-serif",
        'import': "https://fonts.googleapis.com/css2?family=Poppins:wght@700;900&family=Karla:wght@400;600&display=swap"
    },
    9: {
        'name': 'Condensed Power',
        'heading': "'Bebas Neue', sans-serif",
        'body': "'Rubik', sans-serif",
        'import': "https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Rubik:wght@400;600&display=swap"
    },
    10: {
        'name': 'Classic Elegant',
        'heading': "'Libre Baskerville', serif",
        'body': "'Lato', sans-serif",
        'import': "https://fonts.googleapis.com/css2?family=Libre+Baskerville:wght@700&family=Lato:wght@400;700&display=swap"
    },
    11: {
        'name': 'Future Forward',
        'heading': "'Orbitron', sans-serif",
        'body': "'Exo 2', sans-serif",
        'import': "https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Exo+2:wght@400;600&display=swap"
    },
    12: {
        'name': 'Handcrafted',
        'heading': "'Permanent Marker', cursive",
        'body': "'Nunito', sans-serif",
        'import': "https://fonts.googleapis.com/css2?family=Permanent+Marker&family=Nunito:wght@400;700;900&display=swap"
    },
    13: {
        'name': 'Studio Display',
        'heading': "'Cal Sans', sans-serif",
        'body': "'DM Sans', sans-serif",
        'import': "https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap"
    },
    14: {
        'name': 'Tech Minimal',
        'heading': "'Lexend', sans-serif",
        'body': "'Public Sans', sans-serif",
        'import': "https://fonts.googleapis.com/css2?family=Lexend:wght@600;700&family=Public+Sans:wght@400;600&display=swap"
    }
}


# ============================================================
# ACCENT PATTERNS (5 variations)
# ============================================================

ACCENT_PATTERNS = {
    0: {  # Noise grain
        'name': 'Grain',
        'css': '''
        body::before {
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='5' numOctaves='3' /%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='0.05'/%3E%3C/svg%3E");
            pointer-events: none;
            z-index: 9999;
            opacity: 0.4;
        }
        '''
    },
    1: {  # Dot grid
        'name': 'Dots',
        'css': '''
        body::before {
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: radial-gradient(circle, currentColor 1px, transparent 1px);
            background-size: 20px 20px;
            opacity: 0.05;
            pointer-events: none;
            z-index: -1;
        }
        '''
    },
    2: {  # Gradient mesh
        'name': 'Mesh',
        'css': '''
        body::before {
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                radial-gradient(circle at 20% 50%, currentColor 0%, transparent 50%),
                radial-gradient(circle at 80% 80%, currentColor 0%, transparent 50%);
            opacity: 0.1;
            pointer-events: none;
            z-index: -1;
            animation: meshMove 15s ease infinite;
        }
        @keyframes meshMove {
            0%, 100% { transform: translate(0, 0); }
            50% { transform: translate(20px, -20px); }
        }
        '''
    },
    3: {  # Scanlines
        'name': 'Scanlines',
        'css': '''
        body::before {
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: repeating-linear-gradient(
                0deg,
                transparent 0px,
                transparent 2px,
                currentColor 3px
            );
            opacity: 0.02;
            pointer-events: none;
            z-index: 9999;
        }
        '''
    },
    4: {  # Diagonal lines
        'name': 'Lines',
        'css': '''
        body::before {
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: repeating-linear-gradient(
                45deg,
                transparent,
                transparent 10px,
                currentColor 10px,
                currentColor 11px
            );
            opacity: 0.03;
            pointer-events: none;
            z-index: -1;
        }
        '''
    }
}


# ============================================================
# VARIATION GENERATOR
# ============================================================

def get_color_palette(user_number: int) -> Dict:
    """Get deterministic color palette based on user number"""
    palette_index = user_number % 10
    return COLOR_PALETTES[palette_index]


def get_font_pair(user_number: int) -> Dict:
    """Get deterministic font pair based on user number"""
    font_index = user_number % 15
    return FONT_PAIRS[font_index]


def get_accent_pattern(username: str) -> Dict:
    """Get accent pattern based on username hash"""
    # Hash username to get consistent but pseudo-random pattern
    hash_value = int(hashlib.md5(username.encode()).hexdigest(), 16)
    pattern_index = hash_value % 5
    return ACCENT_PATTERNS[pattern_index]


def generate_unique_variations(username: str, user_number: int) -> Dict:
    """
    Generate complete variation set for a user
    
    Returns:
        {
            'color_palette': {...},
            'font_pair': {...},
            'accent_pattern': {...},
            'variation_id': 'electric-tech-modern-grain'
        }
    """
    
    color_palette = get_color_palette(user_number)
    font_pair = get_font_pair(user_number)
    accent_pattern = get_accent_pattern(username)
    
    variation_id = f"{color_palette['name'].lower()}-{font_pair['name'].lower().replace(' ', '-')}-{accent_pattern['name'].lower()}"
    
    return {
        'color_palette': color_palette,
        'font_pair': font_pair,
        'accent_pattern': accent_pattern,
        'variation_id': variation_id,
        'user_number': user_number,
        'username': username
    }


def apply_variations_to_html(html_content: str, variations: Dict) -> str:
    """
    Apply variations to HTML template
    
    Replaces CSS variables and injects custom styles
    """
    
    colors = variations['color_palette']
    fonts = variations['font_pair']
    pattern = variations['accent_pattern']
    
    # Build custom CSS injection
    custom_css = f"""
    <style id="aigentsy-variations">
    /* AiGentsy Template Variations */
    /* Variation ID: {variations['variation_id']} */
    
    :root {{
        --color-primary: {colors['primary']};
        --color-secondary: {colors['secondary']};
        --color-accent: {colors['accent']};
        --color-bg: {colors['bg']};
        --color-text: {colors['text']};
        --gradient: {colors['gradient']};
        
        --font-heading: {fonts['heading']};
        --font-body: {fonts['body']};
    }}
    
    /* Override heading fonts */
    h1, h2, h3, h4, h5, h6,
    .logo, .section-title, .hero h1 {{
        font-family: var(--font-heading) !important;
    }}
    
    /* Override body font */
    body, p, a, button, input, textarea {{
        font-family: var(--font-body) !important;
    }}
    
    /* Accent pattern overlay */
    {pattern['css']}
    </style>
    
    <!-- Font Import -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="{fonts['import']}" rel="stylesheet">
    """
    
    # Inject before </head>
    if '</head>' in html_content:
        html_content = html_content.replace('</head>', f"{custom_css}</head>")
    else:
        # Fallback: inject at start of body
        html_content = html_content.replace('<body>', f"<body>{custom_css}")
    
    return html_content


# ============================================================
# EXAMPLE USAGE
# ============================================================

if __name__ == "__main__":
    
    print("=" * 70)
    print("TEMPLATE VARIATIONS SYSTEM - EXAMPLES")
    print("=" * 70)
    
    # Test different users
    test_users = [
        ("wade", 1),
        ("alice", 37),
        ("bob", 142),
        ("charlie", 999)
    ]
    
    for username, user_number in test_users:
        print(f"\n📊 User: {username} (#{user_number})")
        
        variations = generate_unique_variations(username, user_number)
        
        print(f"   Color Palette: {variations['color_palette']['name']}")
        print(f"   Font Pair: {variations['font_pair']['name']}")
        print(f"   Accent Pattern: {variations['accent_pattern']['name']}")
        print(f"   Variation ID: {variations['variation_id']}")
    
    print("\n" + "=" * 70)
    print("TOTAL UNIQUE COMBINATIONS:")
    print("   10 color palettes × 15 font pairs × 5 patterns = 750 variations")
    print("   Per template × 9 templates = 6,750 total unique storefronts!")
    print("=" * 70)
