def build_comic_layout(outlines, stories, image_paths):
    story_by_panel = {item["panel_number"]: item for item in stories}
    layout = []
    for outline, image_path in zip(outlines, image_paths):
        story = story_by_panel.get(outline["panel_number"], {})
        layout.append({
            "panel_number": outline["panel_number"],
            "title": outline["title"],
            "scene_description": outline["scene_description"],
            "image_prompt": outline["image_prompt"],
            "image_path": image_path,
            "caption": story.get("caption", ""),
            "narration": story.get("narration", ""),
            "dialogue": story.get("dialogue", ""),
        })
    return layout
