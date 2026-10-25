# Plano de Melhorias - FinSavvy

## 1. Documentação das Melhorias

Este documento detalha as melhorias planejadas para o FinSavvy, focando em robustez, segurança de dados e experiência do usuário, seguindo a filosofia de desenvolvimento limpo e minimalista.

### Fatia 1: Robustez no Cadastro de Custos Fixos
*   **Problema:** Atualmente, o sistema tenta salvar custos fixos sem validar o formulário no POST. Isso causa erros (ex: `ValueError`) se o usuário enviar dados inválidos (como letras em campos numéricos ou campos vazios).
*   **Solução:** Adicionar a verificação `form.is_valid()` antes do `save()`. Em caso de erro, o formulário será reexibido com as mensagens de erro nativas do Django.
*   **Impacto:** Impede a corrupção de dados e melhora a experiência do usuário com feedback imediato.

### Fatia 2: CRUD Completo e Seguro (Propriedade de Dados)
*   **Problema:** As views de edição e remoção estão vazias (`pass`). Além disso, não há garantia de que um usuário não possa editar/remover o custo de outro através da URL. No template, o modal de remoção tem IDs fixos, o que impede o funcionamento correto em listas.
*   **Solução:** 
    *   Implementar `edit_custoFixo` e `remove_custoFixo` filtrando sempre por `user=request.user` e `id`.
    *   Parametrizar o template `add_custoFixo.html` para ser reutilizado na edição.
    *   Corrigir os IDs dos modais de remoção na listagem usando o ID do objeto (`{{ custo.id }}`).
*   **Impacto:** Permite o gerenciamento completo dos dados de forma segura e isolada entre usuários.

### Fatia 3: Visualização da Sobra (Adiada)
*   **Status:** **Adiada**.
*   **Motivo:** Para garantir precisão matemática ("centavo certo"), esta funcionalidade deve ser implementada somente após a migração do campo `valor` de `Float` para `Decimal`.
*   **Visão:** Futuramente, o dashboard exibirá: "Entrada (informada) - Soma dos Custos Fixos = Sobra", em linguagem leiga e direta.

### Fila de Pendências ("Depois")
1.  **Migração para Decimal:** Trocar `FloatField` por `DecimalField` no modelo `CustoFixo`.
2.  **Segurança de Deploy:** Configurar `DEBUG=False` e `SECRET_KEY` via variáveis de ambiente antes de qualquer deploy em produção.

---

## 2. Planejamento de Implementação

### Etapa 1: Implementação da Fatia 1 (Guardas de Validação)
*   **Arquivos:** `finsavvy/views.py`, `finsavvy/tests.py`.
*   **Ação:** Corrigir `add_custoFixo` para checar `is_valid()`. Criar teste básico de submissão inválida.

### Etapa 2: Implementação da Fatia 2 (CRUD e Segurança)
*   **Arquivos:** `finsavvy/views.py`, `finsavvy/urls.py`, `finsavvy/templates/pages/list_custosFixos.html`, `finsavvy/templates/pages/add_custoFixo.html`, `finsavvy/tests.py`.
*   **Ação:** Implementar as views, registrar as rotas de edit/delete, ajustar templates e adicionar um teste de isolamento (usuário A não acessa dado do usuário B).
