"""Complete usage example of Agent Skills with Progressive Disclosure

This example demonstrates the Filesystem-Based approach (recommended):
- Phase 1: Discovery (load metadata only in system prompt)
- Phase 2: LLM reads SKILL.md when needed (true progressive disclosure)
- Phase 3: LLM reads resources when needed (scripts, references)

Uses strands_stream TerminalStreamRenderer for colorful streaming output.

For Tool-Based approach, see: 2-skill_tool_with_progressive_disclosure.py
"""
import os
import sys

# ========================================================================
# 核心修复：强制 Python 在 Windows 环境下使用 UTF-8 编码
# 必须放在所有 import 之前，防止第三方库加载时按默认 cp949 读取文件
# ========================================================================
if os.environ.get("PYTHONUTF8") != "1":
    os.environ["PYTHONUTF8"] = "1"
    if sys.platform == "win32":
        os.execv(sys.executable, [sys.executable] + sys.argv)


import asyncio
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))



from strands import Agent
from strands.models.openai import OpenAIModel
from strands_tools import file_read, file_write
from agentskills import discover_skills, generate_skills_prompt, get_bedrock_agent_model
from utils.strands_stream import TerminalStreamRenderer



async def main():
    """Complete usage example with Progressive Disclosure (Phase 1, 2, 3)"""

    print("\n🚀 Agent Skills - Progressive Disclosure Demo\n")

    # ========================================================================
    # Phase 1: Discovery (loads only metadata)
    # ========================================================================
    print("=" * 60)
    print("Phase 1: Discovery (Metadata Only)")
    print("=" * 60)

    skills_dir = Path(__file__).parent.parent / "skills"
    skills = discover_skills(skills_dir)

    print(f"\n✓ Discovered {len(skills)} skills:\n")
    for skill in skills:
        print(f"  📦 {skill.name}")
        print(f"     Description: {skill.description}")
        print(f"     Location: {skill.path}")
        if skill.allowed_tools:
            print(f"     Allowed tools: {skill.allowed_tools}")
        print()

    if not skills:
        print("\n⚠️  No skills found. Create skills in 'skills/' directory.")
        print("Example structure:")
        print("  skills/")
        print("    web-research/")
        print("      SKILL.md")
        return

    # ========================================================================
    # Create agent with system prompt containing skill metadata
    # ========================================================================
    input("\n⏸  Press Enter to continue to generate system prompt...")

    base_prompt = "You are a helpful AI assistant."
    skills_prompt = generate_skills_prompt(skills)
    full_prompt = f"{base_prompt}\n\n{skills_prompt}"

    print("=" * 60)
    print("System Prompt (with skill metadata)")
    print("=" * 60)
    print(full_prompt)
    print("=" * 60)

    # Create agent with file tools
    # LLM will use file_read to load SKILL.md and resources when needed
    QWEN_API_KEY = "xxxxxxx"
    QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    MODEL = "qwen-flash"
    model = OpenAIModel(
        client_args={
            "api_key": QWEN_API_KEY,
            "base_url": QWEN_BASE_URL
        },
        model_id=MODEL,  # 示例模型 ID
        params={
            "temperature": 0.7,
        }
    )
    agent = Agent(
        model=model,
        system_prompt=full_prompt,
        tools=[file_read, file_write],
    )


    # Create TerminalStreamRenderer for streaming output
    renderer = TerminalStreamRenderer()

    # ========================================================================
    # Phase 2: Example 1 - Asking about available skills (metadata only)
    # ========================================================================
    input("\n⏸  Press Enter to continue to Example 1...")

    print("\n" + "=" * 60)
    print("Example 1: Asking about available skills (Phase 1 metadata)")
    print("=" * 60)
    print("\nAsking: 'What skills do you have?'\n")

    renderer.reset()
    async for event in agent.stream_async("What skills do you have?"):
        renderer.process(event)

    print()  # newline after streaming

    # ========================================================================
    # Phase 2: Example 2 - LLM reads SKILL.md when needed
    # ========================================================================
    input("\n⏸  Press Enter to continue to Example 2...")

    if skills:
        print("\n" + "=" * 60)
        print("Example 2: LLM reads SKILL.md on demand (Phase 2)")
        print("=" * 60)
        first_skill = skills[0]
        print(f"\nAsking: 'How do I use the {first_skill.name} skill?'\n")

        renderer.reset()
        async for event in agent.stream_async(
            f"How do I use the {first_skill.name} skill?"
        ):
            renderer.process(event)

        print()
        print("✓ Agent read the SKILL.md only when needed (true progressive disclosure)")

    # ========================================================================
    # Phase 3: Example 3 - LLM reads resource files when needed
    # ========================================================================
    input("\n⏸  Press Enter to continue to Example 3 (Phase 3)...")

    print("\n" + "=" * 60)
    print("Example 3: LLM reads resources on demand (Phase 3)")
    print("=" * 60)

    # Find a skill that mentions resources in its SKILL.md instructions
    skill_with_resources = None
    for skill in skills:
        skill_path = Path(skill.path)
        if not skill_path.exists():
            continue

        try:
            content = skill_path.read_text(encoding="utf-8")
            if "scripts/" in content.lower() or "references/" in content.lower():
                skill_with_resources = skill
                break
        except Exception:
            continue

    if not skill_with_resources:
        print("\nNo skills found that mention resources in their instructions")
        print("(Phase 3 skipped - create a skill with scripts/ or references/ to test)")
        return

    skill_name = skill_with_resources.name
    print(f"\n📦 Testing with skill: '{skill_name}'")
    print("Testing: Agent reads resources based on SKILL.md instructions\n")

    prompt = f"Use the {skill_name} skill. Read the resource files mentioned in SKILL.md instructions."
    print(f"Asking: '{prompt}'\n")

    renderer.reset()
    async for event in agent.stream_async(prompt):
        renderer.process(event)

    print()
    print("✓ Agent read resource files based on SKILL.md instructions (Phase 3)")


if __name__ == "__main__":
    asyncio.run(main())
