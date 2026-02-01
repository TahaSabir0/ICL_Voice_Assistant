#!/usr/bin/env python3
"""
Knowledge Base Generator

Converts raw extracted content (web pages + PDFs) into structured
markdown files organized by category for the RAG system.

Usage:
    python scripts/generate_knowledge_base.py
"""

import json
import re
from pathlib import Path
from typing import Optional


# Configuration
OUTPUT_DIR = Path(__file__).parent.parent / "knowledge_base"
RAW_DIR = OUTPUT_DIR / "raw"
TOOLS_DIR = OUTPUT_DIR / "tools"
GENERAL_DIR = OUTPUT_DIR / "general"


# Tool definitions with metadata
TOOLS = {
    "3d_printing": {
        "name": "3D Printing",
        "description": "A computer aided manufacturing process that builds three-dimensional models out of custom materials, typically plastics.",
        "equipment": [
            {
                "name": "Ender 3 V3 KE",
                "specs": "Build Volume: 8.66\" x 8.66\" x 9.4\"",
                "type": "FDM 3D Printer",
                "manuals": ["Ender-3-v3-ke-user-guide", "3D-Printing-Hardware-Guide-1", "3D-Printing-Software-Guide", "SOP-3D-Printer"],
                "materials": ["PLA", "PETG", "ABS"]
            },
            {
                "name": "Ender CR M4",
                "specs": "Build Volume: 17.7\" x 17.7\" x 18.5\"",
                "type": "FDM 3D Printer (Large Format)",
                "manuals": ["crm4_creality_user-manual", "3D-Printing-Hardware-Guide-1", "3D-Printing-Software-Guide", "SOP-3D-Printer"],
                "materials": ["PLA", "PETG", "ABS"]
            },
            {
                "name": "ELEGOO Saturn 4 Ultra",
                "specs": "Build Volume: 8.6\" x 4.8\" x 8.7\"",
                "type": "Resin 3D Printer",
                "manuals": ["saturn_4_ultra", "SOP-3D-Printer"],
                "materials": ["Resin"]
            },
            {
                "name": "Creality LD-002R",
                "specs": "Print Size: 4.7\" x 2.6\" x 6.3\"",
                "type": "Resin 3D Printer",
                "manuals": ["LD-002R", "SOP-3D-Printer"],
                "materials": ["Resin"]
            }
        ],
        "software": ["Tinkercad (Design)", "Ultimaker Cura (Slicing)", "Chitubox (Resin Slicing)"]
    },
    "laser_cutting": {
        "name": "Laser Cutting",
        "description": "Manufacturing process in which material is vaporized by using a laser beam resulting in high quality, dimensionally accurate cuts and engravings.",
        "equipment": [
            {
                "name": "Omtech 60w Laser",
                "specs": "Work Area: 16\" x 24\"",
                "type": "CO2 Laser Cutter",
                "manuals": ["MF1624-55", "Laser-Cutter-Hardware-Guide", "Laser-Cutter-Software-Guide", "Laser-cutter-materials"],
                "power": "60W"
            },
            {
                "name": "Omtech 130w Laser",
                "specs": "Work Area: 35\" x 55\"",
                "type": "CO2 Laser Cutter (Large Format)",
                "manuals": ["130w-laser-user-manual", "Laser-Cutter-Hardware-Guide", "Laser-Cutter-Software-Guide"],
                "power": "130W"
            }
        ],
        "software": ["LightBurn"],
        "materials": ["Wood", "Acrylic", "Leather", "Cardboard", "Paper", "Fabric"]
    },
    "cnc_machining": {
        "name": "CNC Machining",
        "description": "Computer Numerical Control (CNC) is a subtractive manufacturing process which uses a computer controlled router to remove layers of material from a stock piece.",
        "equipment": [
            {
                "name": "X-Carve",
                "specs": "Cutting Area: 750 x 750 x 65mm (29.5\" x 29.5\" x 2.5\")",
                "type": "CNC Router",
                "manuals": []
            },
            {
                "name": "Carvey",
                "specs": "Cutting Area: 295 x 200 x 65mm (11.6\" x 8\" x 2.5\")",
                "type": "Desktop CNC Router",
                "manuals": []
            }
        ],
        "software": ["Easel by Inventables"],
        "materials": ["Wood", "Soft Metals", "Plastics", "Foam"]
    },
    "sewing_embroidery": {
        "name": "Sewing & Embroidery",
        "description": "Machine with a mechanically driven needle for sewing or stitching fabric.",
        "equipment": [
            {
                "name": "Janome MC 550e Embroidery Machine",
                "specs": "Embroidery only machine",
                "type": "Embroidery Machine",
                "manuals": ["Janome-mc550e-User-Manual", "Embroidery-Hardware-Guide", "Embroidery-Software-Guide"]
            },
            {
                "name": "Janome MC 9850",
                "specs": "Sewing and Embroidery combination machine",
                "type": "Sewing/Embroidery Machine",
                "manuals": ["Janome-MC-9850-User-Manual-1", "Embroidery-Hardware-Guide", "Embroidery-Software-Guide"]
            },
            {
                "name": "Janome HD-3000 Sewing Machine",
                "specs": "Heavy-duty sewing machine",
                "type": "Sewing Machine",
                "manuals": ["Janome-HD-3000-User-Manual"]
            },
            {
                "name": "Janome 792PG Serger",
                "specs": "4-thread serger/overlock machine",
                "type": "Serger",
                "manuals": ["Janome-792pg-Serger-Manual"]
            }
        ],
        "software": ["Digitizer MBX (Embroidery Digitizing)"]
    },
    "virtual_reality": {
        "name": "Virtual Reality",
        "description": "VR headsets generate realistic images, sounds and other sensations that simulate the user's physical presence in virtual environments.",
        "equipment": [
            {
                "name": "Oculus Quest",
                "specs": "Standalone VR headset with 6DOF tracking",
                "type": "Standalone VR Headset",
                "manuals": ["quest"]
            },
            {
                "name": "HTC Vive",
                "specs": "PC-tethered VR headset with room-scale tracking",
                "type": "PC VR Headset",
                "manuals": ["Vive_User_Guide"]
            },
            {
                "name": "Oculus Go",
                "specs": "Standalone VR headset (3DOF)",
                "type": "Standalone VR Headset",
                "manuals": ["go"]
            }
        ],
        "software": ["SteamVR", "Oculus App"]
    },
    "vinyl_cutting": {
        "name": "Vinyl Cutting",
        "description": "Process through which a computer-controlled machine is used to cut out vector based designs from sheets of thin vinyl.",
        "equipment": [
            {
                "name": "53\" Vevor Vinyl Cutter",
                "specs": "Cutting Area: 49.6\" x 300\"",
                "type": "Vinyl Cutter (Large Format)",
                "manuals": ["Vinyl-Cutting-Hardware-Guide", "Vinyl-Cutting-Software-Guide", "SOP-Vinyl"]
            },
            {
                "name": "28\" USCutter TITAN 3",
                "specs": "Cutting Area: 24\" x 300\"",
                "type": "Vinyl Cutter",
                "manuals": ["Titan_Documentation_6_27_2016", "Vinyl-Cutting-Hardware-Guide", "Vinyl-Cutting-Software-Guide", "SOP-Vinyl"]
            },
            {
                "name": "Digital Heat Press",
                "specs": "Bed Size: 15\" x 15\"",
                "type": "Heat Press",
                "manuals": ["A1DogecheeL"]
            },
            {
                "name": "Auto Heat Press",
                "specs": "Bed Size: 15\" x 15\"",
                "type": "Heat Press (Automatic)",
                "manuals": []
            },
            {
                "name": "Curved Heat Press",
                "specs": "For curved surfaces (mugs, etc.)",
                "type": "Heat Press (Curved)",
                "manuals": []
            }
        ],
        "software": ["Vinyl Master"]
    }
}


def load_pdf_text(name: str) -> Optional[str]:
    """Load extracted text from a PDF."""
    txt_path = RAW_DIR / "pdf_text" / f"{name}.txt"
    if txt_path.exists():
        with open(txt_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Skip the header we added
            if "=" * 40 in content:
                content = content.split("=" * 40, 1)[-1]
            return content.strip()
    return None


def create_equipment_markdown(equipment: dict, category: str) -> str:
    """Create markdown content for a single piece of equipment."""
    lines = [
        f"# {equipment['name']}",
        "",
        f"**Type:** {equipment.get('type', 'Equipment')}",
        "",
        f"**Specifications:** {equipment.get('specs', 'See manual')}",
        "",
    ]
    
    # Add materials if available
    if 'materials' in equipment:
        lines.append("**Compatible Materials:** " + ", ".join(equipment['materials']))
        lines.append("")
    
    # Add power if available
    if 'power' in equipment:
        lines.append(f"**Power:** {equipment['power']}")
        lines.append("")
    
    lines.append("---")
    lines.append("")
    
    # Add content from manuals
    if equipment.get('manuals'):
        lines.append("## Documentation")
        lines.append("")
        
        for manual_name in equipment['manuals']:
            manual_text = load_pdf_text(manual_name)
            if manual_text:
                # Get first meaningful section (skip page markers, limit length)
                clean_text = re.sub(r'--- Page \d+ ---\n', '', manual_text)
                # Truncate to reasonable length for each doc
                if len(clean_text) > 8000:
                    clean_text = clean_text[:8000] + "\n\n[Content truncated - see full manual for details]"
                
                lines.append(f"### From: {manual_name}")
                lines.append("")
                lines.append(clean_text)
                lines.append("")
                lines.append("---")
                lines.append("")
    
    return '\n'.join(lines)


def create_category_overview(category_key: str, category_data: dict) -> str:
    """Create overview markdown for a tool category."""
    lines = [
        f"# {category_data['name']}",
        "",
        f"**Category:** {category_key.replace('_', ' ').title()}",
        "",
        "## Overview",
        "",
        category_data['description'],
        "",
        "---",
        "",
        "## Available Equipment",
        "",
    ]
    
    for equip in category_data['equipment']:
        lines.append(f"### {equip['name']}")
        lines.append(f"- **Type:** {equip.get('type', 'Equipment')}")
        lines.append(f"- **Specs:** {equip.get('specs', 'See manual')}")
        if equip.get('materials'):
            lines.append(f"- **Materials:** {', '.join(equip['materials'])}")
        lines.append("")
    
    if category_data.get('software'):
        lines.append("---")
        lines.append("")
        lines.append("## Software")
        lines.append("")
        for sw in category_data['software']:
            lines.append(f"- {sw}")
        lines.append("")
    
    return '\n'.join(lines)


def create_general_info() -> str:
    """Create general ICL information markdown."""
    return """# Innovation & Creativity Lab (ICL)

## About the ICL

The ICL is an open environment where Gettysburg College students, faculty, and staff can create, connect, and explore. The lab offers a continually expanding collection of equipment, tools, and materials to help everyone bring their ideas to life.

## Location

**Address:** 300 N Washington St, Gettysburg, PA 17325  
**Building:** West Building 114 (First floor of Plank Gym)

## Hours

The lab is open to all students, faculty, and staff **24 hours a day, 7 days a week**.

## Available Resources

The ICL provides access to the following types of equipment:

1. **3D Printing** - Build three-dimensional objects from digital models
2. **Laser Cutting** - Cut and engrave materials with precision lasers
3. **CNC Machining** - Computer-controlled subtractive manufacturing
4. **Sewing & Embroidery** - Fabric crafting and custom embroidery
5. **Virtual Reality** - Immersive VR experiences and development
6. **Vinyl Cutting** - Create custom decals, stickers, and heat transfers
7. **Sublimation Printing** - Transfer designs onto various materials

## Contact

For more information about the ICL, visit the lab or contact staff during staffed hours.

## Social Media

- Twitter: @InnovationandC5
- Instagram: @innovationandcreativitylab
- TikTok: @innovationandc5
"""


def sanitize_filename(name: str) -> str:
    """Create a safe filename from equipment name."""
    # Remove special characters and replace spaces
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'\s+', '_', name)
    return name.lower()


def main():
    """Main knowledge base generator function."""
    print("=" * 60)
    print("Knowledge Base Generator")
    print("=" * 60)
    
    # Ensure directories exist
    for category in TOOLS.keys():
        (TOOLS_DIR / category).mkdir(parents=True, exist_ok=True)
    GENERAL_DIR.mkdir(parents=True, exist_ok=True)
    
    # Generate category overviews and equipment files
    stats = {"categories": 0, "equipment": 0, "total_chars": 0}
    
    for category_key, category_data in TOOLS.items():
        print(f"\n[{category_data['name']}]")
        category_dir = TOOLS_DIR / category_key
        
        # Create category overview
        overview_content = create_category_overview(category_key, category_data)
        overview_path = category_dir / "_overview.md"
        with open(overview_path, 'w', encoding='utf-8') as f:
            f.write(overview_content)
        print(f"  ✓ Overview: {overview_path.name}")
        stats["categories"] += 1
        stats["total_chars"] += len(overview_content)
        
        # Create equipment files
        for equipment in category_data['equipment']:
            equip_content = create_equipment_markdown(equipment, category_key)
            filename = sanitize_filename(equipment['name']) + ".md"
            equip_path = category_dir / filename
            
            with open(equip_path, 'w', encoding='utf-8') as f:
                f.write(equip_content)
            
            print(f"  ✓ Equipment: {filename} ({len(equip_content):,} chars)")
            stats["equipment"] += 1
            stats["total_chars"] += len(equip_content)
    
    # Create general ICL info
    print("\n[General Information]")
    general_content = create_general_info()
    general_path = GENERAL_DIR / "icl_info.md"
    with open(general_path, 'w', encoding='utf-8') as f:
        f.write(general_content)
    print(f"  ✓ Created: {general_path.name}")
    stats["total_chars"] += len(general_content)
    
    # Print summary
    print("\n" + "=" * 60)
    print("GENERATION COMPLETE")
    print("=" * 60)
    print(f"Categories: {stats['categories']}")
    print(f"Equipment files: {stats['equipment']}")
    print(f"Total content: {stats['total_chars']:,} characters")
    print(f"\nOutput: {TOOLS_DIR}")


if __name__ == "__main__":
    main()
