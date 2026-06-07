class ResponseBuilder:

    def build(self, resultado: dict):
        status = resultado.get("status")

        if status == "ok":
            return self._sucesso(resultado)

        if status == "erro":
            return self._erro(resultado)

        return "⚠️ Resposta inválida do sistema."

    # =========================
    # SUCESSO
    # =========================
    def _sucesso(self, resultado):
        tipo = resultado.get("tipo")
        dados = resultado.get("dados", {})

        if tipo == "venda":
            return self._venda_sucesso(dados)

        return "✅ Operação concluída com sucesso."

    def _venda_sucesso(self, d):
        return (
            f"Cooper: Venda registrada com sucesso!\n\n"
            f"📦 Produto: {d['produto']}\n"
            f"🔢 Código: {d['codigo']}\n"
            f"📊 Quantidade: {d['quantidade']}\n"
            f"💰 Preço unitário: R$ {d['preco_unitario']:.2f}\n"
            f"💵 Total: R$ {d['total']:.2f}\n"
            f"🕒 Data: {d['data']}"
        )

    # =========================
    # ERROS
    # =========================
    def _erro(self, resultado):
        erro = resultado.get("erro")
        mensagem = resultado.get("mensagem", "Erro desconhecido")

        if erro == "estoque_insuficiente":
            d = resultado.get("dados", {})
            return (
                f"⚠️ Estoque insuficiente!\n\n"
                f"📦 Produto: {d.get('produto')}\n"
                f"📊 Disponível: {d.get('estoque_disponivel')}\n"
                f"❌ Solicitado: {d.get('solicitado')}"
            )

        return f"⚠️ {mensagem}"