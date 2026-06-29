# Image to Editable draw.io Skill

这个 skill 用于把任意一张扁平图片、截图、信息图、流程图、架构图、界面图、海报或手绘草图重建为可编辑的多图层 draw.io / diagrams.net 文件。

核心策略：复杂背景保留或修复为 PNG；清晰小元素生成 SVG；文字、箭头、线条、框、流程节点和标注尽量用 draw.io 原生对象重建。

主要文件：

- `SKILL.md`：完整工作流程说明；
- `templates/asset_manifest_template.json`：通用元素清单模板；
- `scripts/create_drawio_from_manifest.py`：根据 manifest 自动组合 draw.io 文件；
- `scripts/package_drawio_project.py`：打包项目文件；
- `examples/asset_manifest_example.json`：通用示例清单；
- `examples/assets/`：示例素材。
