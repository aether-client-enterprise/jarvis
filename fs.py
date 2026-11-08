# *Acesso ao sistema de arquivos do PC — leitura, escrita, navegação e exclusão total.*
import os
from pathlib import Path

class FS:
    def __init__(self):
        self.roots = [f"{d}:\\" for d in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if Path(f"{d}:\\").exists()]

    def browse(self, path=""):
        if not path:
            return {"roots": self.roots, "items": []}
        p = Path(path)
        if not p.exists():
            return {"error": "Caminho não encontrado"}
        if not p.is_dir():
            return {"error": "Não é um diretório"}
        items = []
        try:
            for child in sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                try:
                    st = child.stat()
                    items.append({
                        "name": child.name,
                        "path": str(child),
                        "is_dir": child.is_dir(),
                        "size": st.st_size if child.is_file() else None,
                    })
                except Exception:
                    continue
        except PermissionError:
            return {"error": "Acesso negado", "path": str(p)}
        except Exception as e:
            return {"error": str(e)}
        return {"path": str(p), "items": items}

    def read(self, path):
        p = Path(path)
        if not p.exists():
            return {"error": "Arquivo não encontrado"}
        if p.is_dir():
            return {"error": "É um diretório, use listar para navegar"}
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
            return {"path": str(p), "size": p.stat().st_size, "content": text[:500000]}
        except Exception as e:
            return {"error": str(e)}

    def write(self, path, content):
        p = Path(path)
        try:
            if p.parent and not p.parent.exists():
                p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            return {"status": "ok", "path": str(p), "size": p.stat().st_size, "message": "Arquivo criado/atualizado com sucesso."}
        except Exception as e:
            return {"error": str(e)}

    def delete(self, path):
        p = Path(path)
        try:
            if p.is_dir():
                import shutil
                shutil.rmtree(p)
            else:
                p.unlink()
            return {"status": "ok", "message": "Excluído com sucesso."}
        except Exception as e:
            return {"error": str(e)}

    def search(self, query, root=""):
        results = []
        base_list = [Path(root)] if root else [Path(r) for r in self.roots]
        for base in base_list:
            try:
                for p in base.rglob(f"*{query}*"):
                    if len(results) >= 200:
                        break
                    results.append({"name": p.name, "path": str(p), "is_dir": p.is_dir()})
            except Exception:
                continue
        return {"query": query, "results": results}
