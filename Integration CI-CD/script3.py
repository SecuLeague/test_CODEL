import subprocess
from github import Github
import shutil
import time
import os
from tabulate import tabulate  # Pour afficher le tableau dans un format lisible

# Dictionnaire des descriptions et IDs associés à chaque cas global
descriptions_ideas_ids = {
    'Deploiement automatisé': ("Déploiement sans intervention humaine réussi.", "ID: 1", 1),
    'Installation des tools DevOps': ("Outils DevOps installés et fonctionnels", "ID: 2", 2),
    'Integration des services': ("Services interconnectés et communiquant efficacement.", "ID: 3", 3),
    'Pratiques DevOps': ("Principes DevOps appliqués avec succès", "ID: 4", 4)
}

def execute_ansible_playbook(playbook_path, case_id, global_case_name):
    """
    Exécute un playbook Ansible avec la commande ansible-playbook et génère un rapport.
    """
    test_result = "Échec"
    error_message = ""
    start_time = time.time()  # Capturer le temps de début de l'exécution

    try:
        # Définir l'environnement pour éviter les avertissements Ansible
        env = os.environ.copy()
        env["ANSIBLE_STDOUT_CALLBACK"] = "debug"  # Affiche les informations de débogage et évite les avertissements

        command = [
            "ansible-playbook",
            playbook_path,
            "--extra-vars",
            "VAULT_TOKEN=hvs.CAESIG6Np0e1q8slYdFzjd9Yu9eGrsYJU088WLkmkZnkj-IUGh4KHGh2cy5DRng2RlZRNGsyekRleWtkYVRMOGR6TDE",
            "-i", "localhost,",  # Indiquer explicitement localhost comme hôte
            "--connection", "local"  # Utiliser la connexion locale pour éviter les avertissements
        ]

        # Exécution du playbook avec subprocess et l'environnement ajusté
        result = subprocess.run(command, text=True, capture_output=True, env=env)

        # Affichage de la sortie standard et des erreurs
        print(f"Sortie du playbook {playbook_path}: {result.stdout}")
        if result.stderr:
            print(f"Erreurs (le cas échéant) du playbook {playbook_path}: {result.stderr}")
            error_message = result.stderr
        else:
            # Analyser les résultats dans la sortie pour déterminer si le test a échoué ou non
            if "failed=0" in result.stdout:  # Vérification si aucun échec n'est reporté
                test_result = "Passed"
            elif "failed=1" in result.stdout:  # Vérification si un échec est reporté
                test_result = "Failed"
            else:
                test_result = "Échec"  # Par défaut en cas de résultat indéfini

    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de l'exécution du playbook {playbook_path}: {e}")
        print(f"Sortie d'erreur: {e.stderr}")
        error_message = e.stderr
    finally:
        # Calculer le temps d'exécution
        execution_time = time.time() - start_time

        # Récupérer la description et l'ID à partir du dictionnaire
        case_description, case_id_label, case_id_number = descriptions_ideas_ids.get(global_case_name, ("Description non disponible", "ID: N/A", 0))

        # Retourner les informations du test pour générer le rapport
        return {
            "ID": case_id_number,
            "Cas_de_test_global": global_case_name,
            "Sous_cas_de_test": playbook_path.split('/')[-1].replace(".yml", ""),  # Supprimer l'extension .yml
            "Test_Description": case_description,
            "Test_Result": test_result,
            "Execution_Time": f"{execution_time:.2f} secondes",
            "Test_Execution_Date": time.strftime('%Y-%m-%d %H:%M:%S'),
            "Tester_Name": "Walid Toumi",  # Nom du testeur
            "Error_Message": error_message if test_result == "Failed" else "Aucun"
        }

def generate_test_report(test_results):
    """
    Affiche un rapport de test sous forme de tableau avec les résultats collectés.
    """
    headers = ["ID", "Sous-cas de test", "Test_Description", "Cas de test global", "Test_Result", "Execution_Time", "Test_Execution_Date", "Tester_Name", "Error_Message"]

    rows = []
    for result in test_results:
        row = [
            result["ID"],
            result["Sous_cas_de_test"],
            result["Test_Description"],
            result["Cas_de_test_global"],
            result["Test_Result"],
            result["Execution_Time"],
            result["Test_Execution_Date"],
            result["Tester_Name"],
            result["Error_Message"]
        ]
        rows.append(row)

    # Afficher le rapport sous forme de tableau
    print("\nRapport de test :")
    print(tabulate(rows, headers=headers, tablefmt="grid"))

def get_repository_contents(token, repo_name, local_path):
    test_results = []  # Liste pour stocker les résultats des tests

    try:
        # Création de l'objet Github avec le token
        g = Github(token)

        # Accéder au dépôt GitHub
        print(f"Accès au dépôt GitHub: {repo_name}...")
        repo = g.get_repo(repo_name)

        # Récupérer le contenu du répertoire racine
        contents = repo.get_contents("")

        if not contents:
            print(f"Le dépôt {repo_name} est vide ou ne contient pas de fichiers.")
            return

        print(f"Contenu récupéré du dépôt {repo_name}: {len(contents)} éléments")

        # Cloner le dépôt localement pour avoir les fichiers disponibles sur le disque
       # if os.path.exists(local_path):
        #    shutil.rmtree(local_path)  # Supprime l'ancien répertoire s'il existe
       # os.makedirs(local_path)  # Crée un nouveau répertoire pour cloner le dépôt

        # Utilisation de Git pour cloner le dépôt localement
        subprocess.run(["git", "clone", f"https://github.com/{repo_name}.git", local_path])

        # Fonction pour explorer récursivement les répertoires et afficher leur contenu
        def explore_directory(path, contents, case_id):
            for file_content in contents:
                # Si c'est un répertoire, on explore récursivement ce répertoire
                if file_content.type == "dir":
                    print(f"Répertoire trouvé : {file_content.path}")
                    sub_contents = repo.get_contents(file_content.path)
                    print(f"Contenu du répertoire {file_content.path}:")
                    explore_directory(file_content.path, sub_contents, case_id)  # Appel récursif pour explorer le sous-répertoire
                else:
                    # Si c'est un fichier YAML, on l'exécute
                    if file_content.name.endswith(".yml"):
                        # Calcul du chemin relatif du fichier dans le répertoire cloné
                        playbook_path = os.path.join(local_path, file_content.path)
                        print(f"Exécution du playbook {playbook_path}...")

                        # Définir un ID et le nom du cas global pour chaque playbook
                        case_id = (case_id % 4) + 1  # Assigner un ID de test entre 1 et 4
                        global_case_name = file_content.path.split("/")[0]  # Premier segment du chemin comme cas global

                        # Exécution du playbook et stockage du résultat
                        test_result = execute_ansible_playbook(playbook_path, case_id, global_case_name)
                        test_results.append(test_result)  # Ajouter le résultat du test à la liste

        # Explorer le répertoire racine du dépôt cloné
        explore_directory("", contents, 1)

    except Exception as e:
        print(f"Erreur lors de la récupération des contenus du dépôt : {e}")

    # Une fois tous les tests exécutés, générer le rapport
    generate_test_report(test_results)

if __name__ == "__main__":
    # Définir le token GitHub directement dans le script
    github_token = "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" # Remplacez ceci par votre token GitHub
    local_path = "test_CODEL"  # Chemin local pour cloner le dépôt

    if github_token:
        repo_name = "SecuLeague/test_CODEL"  # Utilisation du dépôt spécifique
        get_repository_contents(github_token, repo_name, local_path)
    else:
        print("Erreur : Le token GitHub n'est pas défini.")

