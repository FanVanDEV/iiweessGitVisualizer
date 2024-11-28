import os
import subprocess
import zlib
from pathlib import Path


def get_all_commits_info(repo_path, target_file):
    try:
        if ".git" in os.listdir(repo_path):
            repo_path = os.path.join(repo_path, ".git")
        branches_path = os.path.join(repo_path, "refs", "heads")

        if not os.path.exists(branches_path):
            raise FileNotFoundError("Не найдены ветки в репозитории.")

        dict_info = {}
        objects_path = os.path.join(repo_path, "objects")

        for root, _, files in os.walk(branches_path):
            for branch_file in files:
                branch_path = os.path.join(root, branch_file)
                with open(branch_path, "r") as bref:
                    last_commit_hash = bref.read().strip()
                commits_bypassing(objects_path, last_commit_hash, dict_info, target_file)

        return dict_info
    except FileNotFoundError:
        print(f"Путь к репозиторию указан неверно. Проверьте аргументы и попробуйте снова.")
        return {}


def commits_bypassing(objects_path, commit_hash, dict_info, target_file):
    if commit_hash in dict_info:
        return

    commit_path = os.path.join(objects_path, commit_hash[:2], commit_hash[2:])
    try:
        with open(commit_path, "rb") as info:
            data = zlib.decompress(info.read()).decode('utf-8').splitlines()
    except FileNotFoundError:
        print(f"Объект {commit_hash} не найден. Возможно, репозиторий поврежден.")
        return

    tree_hash, parents, message = None, [], ""
    for line in data:
        if line.startswith("parent"):
            parents.append(line.split()[1])
        elif not line.startswith(("author", "committer")):
            message = line

    dict_info[commit_hash] = [parents, message]

    for parent in parents:
        commits_bypassing(objects_path, parent, dict_info, target_file)


def get_files_from_tree(commit_hash):
    try:
        files = subprocess.check_output(['git', 'show', '--pretty=format:', '--name-only', commit_hash],
                                        text=True).strip().split('\n')
        return files

    except FileNotFoundError:
        print(f"Ошибка: Объект {commit_hash} не найден.")
        return []


def generate_plantuml_graph(commits):
    lines = ["@startuml"]
    for commit, info in commits.items():
        lines.append(f'{commit} : {info[1]}')
        for parent in info[0]:
            if parent in commits.keys():
                lines.append(f'{parent} --> {commit}')
    lines.append("@enduml")
    return "\n".join(lines)


def save_plantuml_file(graph_data, output_path):
    """Сохраняет данные PlantUML в файл."""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(graph_data)


def render_plantuml(plantuml_path, uml_file, output_image):
    subprocess.run(
        ["java", "-jar", plantuml_path, "-tpng", uml_file, "-o", output_image],
    )


def filter_commits_with_file(commits, target_file):
    filtered_commits = {}

    for commit_hash, (parents, message) in commits.items():
        files_from_tree = get_files_from_tree(commit_hash)
        if target_file in files_from_tree:
            filtered_commits[commit_hash] = (parents, message)
            continue

    for commit_hash, (parents, message) in filtered_commits.items():
        filtered_parents = [parent for parent in parents if parent in filtered_commits]

        filtered_commits[commit_hash] = (filtered_parents, message)

    return filtered_commits


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Визуализатор графа зависимостей Git.")
    parser.add_argument("--plantuml", required=True, help="Путь к программе PlantUML (jar-файл).")
    parser.add_argument("--repo", required=True, help="Путь к анализируемому git-репозиторию.")
    parser.add_argument("--output", required=True, help="Путь для сохранения графа в формате PNG.")
    parser.add_argument("--file", required=True, help="Файл, для которого строится граф.")

    args = parser.parse_args()

    repo_path = Path(args.repo).resolve()
    plantuml_path = Path(args.plantuml).resolve()
    output_image = Path(args.output).resolve()
    target_file = args.file

    if not (repo_path / ".git").exists():
        print(f"Ошибка: {repo_path} не является git-репозиторием.")
        return

    commits_info = get_all_commits_info(repo_path, target_file)

    if not commits_info.items():
        print("Нет подходящих коммитов для указанного файла.")
        return

    # commits_info = filter_commits_with_file(commits_info, target_file)
    plantuml_graph = generate_plantuml_graph(commits_info)

    uml_file = output_image.with_suffix(".uml")
    save_plantuml_file(plantuml_graph, uml_file)

    render_plantuml(plantuml_path, uml_file, output_image)

    print(f"Граф зависимостей успешно сохранён в {output_image}")


if __name__ == "__main__":
    main()
