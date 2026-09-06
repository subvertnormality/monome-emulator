"""Run one bounded Paranoia plan review using its installed MCP Python runtime.

This is an operator-invoked planning helper, not an autonomous delivery driver.
Run with the Python environment that has the MCP client installed; pass the
installed paranoia-local executable explicitly. Outputs remain in the workspace.
"""

import argparse
import asyncio
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--engine", default="claude")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--output", default="docs/delivery/reviews/P0-raw.json")
    parser.add_argument("--question-file", help="Use a focused Paranoia query instead of another critique")
    args = parser.parse_args()
    repo = Path(args.repo).resolve()
    paths = ["docs/delivery/PLAN.md", "docs/delivery/ACCEPTANCE.md",
             "docs/delivery/RUNBOOK.md", "docs/delivery/DECISIONS.md"]
    packet = "\n\n".join(f"# FILE: {p}\n\n{(repo / p).read_text()}" for p in paths)
    output = repo / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    request = {
        "repo_path": str(repo), "plan_text": packet, "engine": args.engine,
        "round": 1, "class_closure": False, "claim_verification": False,
        "web_search": False, "effort": "medium",
        "stakes": "Trusted single-user local Mosaic development emulator. WSL2 Ubuntu 20.04 first, native Linux later. MIDI-only, no physical hardware or audio acceptance. Realistic risks: misleading green tests, runtime/API mismatch, unusable LLM control/diagnostics, accidental local project clobber, wasted engineering. No finance, hostile actors, multi-tenancy or hard-real-time hardware certification. One bounded structural review; empirical external premises are explicitly gated in C00 and later cards.",
        "context": "The user requested a proportionate adaptation of Parallax's heavyweight process. This is a planning deliverable, not implementation. Mosaic inspection checkout exists at upstream/mosaic. No emulator has been built or tested. Existing Ubuntu 20.04 must be probed before suggesting any distro migration. Manual testing is forbidden as acceptance; LLMs need real runtime interaction and observations.",
        "focus": "Find only substantive in-scope delivery gaps, dependency cycles, untestable acceptance, circular oracles, false-green escape routes, unsupported runtime assumptions, or disproportionate governance. Check whether a fresh execution agent can deliver end to end. Cite document and section/line. Limit to the most consequential findings; no speculative hardening or unlimited review machinery.",
    }
    tool_name = "critique_plan"
    if args.question_file:
        tool_name = "query"
        request = {
            "repo_path": str(repo), "engine": args.engine,
            "question": (repo / args.question_file).read_text(),
            "files": [{"path": p, "reason": "Updated delivery contract"} for p in paths]
                + [{"path": "docs/delivery/reviews/P0-triage.md", "reason": "Findings and fixes"}],
            "web_search": False, "effort": "medium",
        }
    record = {"started_at": datetime.now(timezone.utc).isoformat(),
              "packet_sha256": hashlib.sha256(packet.encode()).hexdigest(),
              "files": paths, "tool": tool_name, "request": request}
    output.write_text(json.dumps(record, indent=2))
    params = StdioServerParameters(command=args.server, args=["--engine", args.engine])
    try:
        async with asyncio.timeout(args.timeout):
            with output.with_suffix(".stderr.log").open("w") as errlog:
                async with stdio_client(params, errlog=errlog) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        listed = await session.list_tools()
                        tool = next(t for t in listed.tools if t.name == tool_name)
                        supported = tool.inputSchema.get("properties", {})
                        unknown = set(request) - set(supported)
                        if unknown:
                            raise ValueError(f"Installed {tool_name} does not support {sorted(unknown)}")
                        result = await session.call_tool(tool_name, request)
                        record["result"] = result.model_dump(mode="json")
                        result_text = "\n".join(
                            getattr(block, "text", "") for block in result.content
                        )
                        failed = result.isError or any(marker in result_text for marker in
                            ("REVIEW FAILED", "[paranoia-local error]", "STATE-UNAVAILABLE"))
                        record["status"] = "tool_error" if failed else "returned"
    except Exception as exc:
        record["status"] = "error"
        record["error"] = f"{type(exc).__name__}: {exc}"
    record["finished_at"] = datetime.now(timezone.utc).isoformat()
    output.write_text(json.dumps(record, indent=2))
    print(json.dumps({"output": str(output), "status": record["status"]}))
    if record["status"] != "returned":
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
