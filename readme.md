Pour installer l'env : 
> Dans le dossier du projet faire : python3 -m venv env
> Puis faire : source env/bin/activate/
> Puis faire : pip install -r requirement.txt

Pour tester le server mcp : 
> Activer l'env avec: source env/bin/activate/
> Aller dans le dossier mcp-invalidator : cd mcp-invalidator/
> docker run --rm mcp-invalidator
> mcp dev server.py
> Une interface sur le navigateur devrait s'afficher, on va alors mettre dans les paramètres à gauche :
> Transport Type : STDIO
> Command : python3
> Arguments : server.py
> On appuie ensuite sur Connect
> On devrait alors voir une autre interface au milieu à droite
> On va sur l'onglet Tools
> On sélectionne Invalidate 
> On met la conjecture et run voila

