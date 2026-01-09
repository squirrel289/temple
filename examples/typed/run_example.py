from temple.typed_ast import Block, Text, Expression, If, For
from temple.typed_renderer import evaluate_ast, json_serialize, markdown_serialize


def build_example():
    # Template: "Hello {{ user.name }}" and list of skills
    root = Block([
        Text("Hello "),
        Expression("user.name"),
        Text("\nSkills:"),
        For("skill", "user.skills", Block([Text("- "), Expression("skill")])),
    ])
    return root


def main():
    ctx = {"user": {"name": "Alice", "skills": ["Python", "Templating"]}}
    root = build_example()
    result = evaluate_ast(root, ctx)
    print("=== JSON IR ===")
    print(json_serialize(result.ir))
    print("=== MARKDOWN ===")
    print(markdown_serialize(result.ir))


if __name__ == "__main__":
    main()
