# Plano de Implementação – Extensão de Custos

## Visão geral
O objetivo é ampliar o módulo de *custos* já existente para incluir:

1. **Custos Variáveis** com categoria.
2. **Custos de Compras** (QR‑Code / código‑barra).
3. **Custos de Combustível** associado a veículos e cálculo de autonomia.
4. **Custos de Manutenção** com trocas de óleo e previsão de alertas.
5. **Relatório Mensal** compacto e versão avançada com estatísticas.

A proposta segue a arquitetura de **Monolito Modular**: cada funcionalidade é encapsulada numa *sub‑aplicação* (`app`) com seus próprios modelos, formulários, URLs, vistas e templates. O aplicativo principal `finsavvy` permanece como ponto de integração.

## Plano por Módulos

| Módulo | Prioridade | Responsável | Estimativa | Status |
|--------|------------|-------------|------------|--------|
| **CustoVariavel** | 1 | Eu | 1 dia | 🚧 |
| **CustoCompra** | 1.5 | Eu | 1 dia | 🚧 |
| **Veiculo** | 2 | Eu | 1 dia | 🚧 |
| **CustoCombustivel** | 3 | Eu | 1 dia | 🚧 |
| **Manutencao** | 4 | Eu | 1 dia | 🚧 |
| **Relatorio** | 5 | Eu | 2 dias | 🚧 |
| **Integração & Testes** | 6 | Eu | 1 dia | 🚧 |

> **Observação**: A ordem reflete dependências (veículo → combustível → manutenção). O relatório depende de todas as anteriores.

## Dependências Extras
- `pyzbar` + `Pillow` (para decodificação de QR‑Code).
- `numpy` (para estatísticas).
- `pandas` (para exportação CSV avançada).

## Diagrama de Casos de Uso (PlantUML)
Para gerar diagramas, copie o conteúdo abaixo para um editor que suporte PlantUML.

```plantuml
@startuml
left to right direction
actor User as "Usuário autenticado"

package "Custos" {
  rectangle "CustoVariavel" {
    User -> CustoVariavel : Cadastra
    User -> CustoVariavel : Edita
    User -> CustoVariavel : Exclui
  }
  rectangle "CustoCompra" {
    User -> CustoCompra : Importa QR
    User -> CustoCompra : Edita
    User -> CustoCompra : Exclui
  }
  rectangle "Veiculo" {
    User -> Veiculo : Cadastra
    User -> Veiculo : Edita
    User -> Veiculo : Exclui
  }
  rectangle "Combustível" {
    User -> CustoCombustivel : Cadastra
    User -> CustoCombustivel : Visualiza
  }
  rectangle "Manutenção" {
    User -> Manutencao : Cadastra
    User -> Manutencao : Visualiza
  }
}

note right: O Relatório
User -- -> Relatorio : Visualiza (mensal)
User -- -> Relatorio : Exporta CSV
```
```

## Estrutura de Diretórios

```
/finsavvy
    ├─ models.py          # Modelos adicionais
    ├─ forms.py
    ├─ views.py
    ├─ urls.py
    ├─ templates/
        ├─ pages/
            ├─ list_custosVariavel.html
            ├─ add_custoVariavel.html
            ├─ list_veiculos.html
            ├─ add_veiculo.html
            ├─ ...
```

## Próximos passos
1. Criar modelos e migrações.
2. Criar formulários.
3. Implementar vistas e templates.
4. Gerar relatórios em `/relatorios/`.
5. Escrever testes unitários.
6. Atualizar documentação.

---
> Este documento será atualizado conforme o progresso.
