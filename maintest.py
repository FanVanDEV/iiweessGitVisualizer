import unittest
from unittest.mock import patch, MagicMock
import subprocess
from pathlib import Path
import os
import zlib

from main import save_plantuml_file, render_plantuml, generate_plantuml_graph, filter_commits_with_file, \
    get_files_from_tree, get_all_commits_info


class MainTest(unittest.TestCase):

    @patch('os.listdir')
    def test_get_all_commits_info_repo_not_found(self, mock_listdir):
        # Проверяем случай, когда не найден .git в директории
        mock_listdir.return_value = []
        result = get_all_commits_info("/path/to/repo", "target_file")
        self.assertEqual(result, {})

    @patch('subprocess.check_output')
    def test_get_files_from_tree(self, mock_subprocess):
        mock_subprocess.return_value = "file1\nfile2"
        result = get_files_from_tree("commit_hash")
        self.assertEqual(result, ['file1', 'file2'])

    @patch('subprocess.check_output')
    def test_filter_commits_with_file(self, mock_subprocess):
        mock_subprocess.return_value = "file1\nfile2"

        commits = {
            'commit1': (['parent1'], 'message1'),
            'commit2': (['parent2'], 'message2'),
            'commit3': (['parent3'], 'message3')
        }

        target_file = 'file1'
        filtered_commits = filter_commits_with_file(commits, target_file)
        self.assertIn('commit1', filtered_commits)

    @patch('subprocess.check_output')
    def test_generate_plantuml_graph(self, mock_subprocess):
        # Проверяем генерацию графа PlantUML
        commits = {
            'commit1': (['parent1'], 'message1'),
            'commit2': (['parent1'], 'message2')
        }
        graph = generate_plantuml_graph(commits)
        self.assertIn('commit1 : message1', graph)
        self.assertIn('parent1 --> commit1', graph)

    @patch('subprocess.run')
    def test_render_plantuml(self, mock_run):
        # Проверяем рендеринг графа PlantUML
        plantuml_path = "/path/to/plantuml.jar"
        uml_file = "/path/to/graph.uml"
        output_image = "/path/to/output.png"

        render_plantuml(plantuml_path, uml_file, output_image)
        mock_run.assert_called_once_with(
            ["java", "-jar", plantuml_path, "-tpng", uml_file, "-o", output_image]
        )

    @patch('builtins.open', new_callable=MagicMock)
    def test_save_plantuml_file(self, mock_open):
        # Проверяем сохранение графа в файл
        graph_data = "@startuml\ncommit1 : message1\n@enduml"
        output_path = Path('/path/to/output.puml')

        save_plantuml_file(graph_data, output_path)
        mock_open.assert_called_once_with(output_path, 'w', encoding='utf-8')


if __name__ == '__main__':
    unittest.main()
