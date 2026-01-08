# financeiro/views.py
from rest_framework.decorators import action
from rest_framework import viewsets, permissions, decorators
from rest_framework.response import Response
from financeiro.tasks import enviar_alerta_email
from financeiro.models import Mensalidade, Pagamento, Salario, Fatura, AlertaEnviado
from financeiro.serializers import (
    MensalidadeSerializer,
    PagamentoSerializer,
    SalarioSerializer,
    FaturaSerializer,
    AlertaEnviadoSerializer,
)


class MensalidadeViewSet(viewsets.ModelViewSet):
    queryset = Mensalidade.objects.all()
    serializer_class = MensalidadeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_update(self, serializer):
        instance = serializer.save()
        instance.atualizar_status()

    @decorators.action(detail=False, methods=["get"])
    def pendentes(self, request):
        qs = Mensalidade.objects.pendentes()
        return Response(MensalidadeSerializer(qs, many=True).data)

    @decorators.action(detail=False, methods=["get"])
    def atrasadas(self, request):
        qs = Mensalidade.objects.atrasadas()
        return Response(MensalidadeSerializer(qs, many=True).data)

    @decorators.action(detail=False, methods=["get"])
    def pagas(self, request):
        qs = Mensalidade.objects.pagas()
        return Response(MensalidadeSerializer(qs, many=True).data)


class PagamentoViewSet(viewsets.ModelViewSet):
    queryset = Pagamento.objects.all()
    serializer_class = PagamentoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        pagamento = serializer.save()
        pagamento.mensalidade.atualizar_status()


class SalarioViewSet(viewsets.ModelViewSet):
    queryset = Salario.objects.all()
    serializer_class = SalarioSerializer
    permission_classes = [permissions.IsAuthenticated]

    @decorators.action(detail=False, methods=["get"])
    def pagos(self, request):
        qs = Salario.objects.pagos()
        return Response(SalarioSerializer(qs, many=True).data)

    @decorators.action(detail=False, methods=["get"])
    def pendentes(self, request):
        qs = Salario.objects.pendentes()
        return Response(SalarioSerializer(qs, many=True).data)


class FaturaViewSet(viewsets.ModelViewSet):
    queryset = Fatura.objects.all()
    serializer_class = FaturaSerializer
    permission_classes = [permissions.IsAuthenticated]

    @decorators.action(detail=False, methods=["get"])
    def vencidas(self, request):
        qs = Fatura.objects.vencidas()
        return Response(FaturaSerializer(qs, many=True).data)

    @decorators.action(detail=False, methods=["get"])
    def pagas(self, request):
        qs = Fatura.objects.pagas()
        return Response(FaturaSerializer(qs, many=True).data)

    @decorators.action(detail=False, methods=["get"])
    def pendentes(self, request):
        qs = Fatura.objects.pendentes()
        return Response(FaturaSerializer(qs, many=True).data)


class AlertaEnviadoViewSet(viewsets.ModelViewSet):
    queryset = AlertaEnviado.objects.all()
    serializer_class = AlertaEnviadoSerializer
    permission_classes = [permissions.IsAuthenticated]

    @decorators.action(detail=False, methods=["get"])
    def enviados(self, request):
        qs = AlertaEnviado.objects.enviados()
        return Response(AlertaEnviadoSerializer(qs, many=True).data)

    @decorators.action(detail=False, methods=["get"])
    def falhos(self, request):
        qs = AlertaEnviado.objects.falhos()
        return Response(AlertaEnviadoSerializer(qs, many=True).data)

    @decorators.action(detail=False, methods=["get"])
    def pendentes(self, request):
        qs = AlertaEnviado.objects.pendentes()
        return Response(AlertaEnviadoSerializer(qs, many=True).data)

    @decorators.action(detail=False, methods=["post"])
    def reprocessar(self, request):
        falhos = AlertaEnviado.objects.filter(status="FALHA NO ENVIO")
        reprocessados = []
        for alerta in falhos:
            enviar_alerta_email.delay(alerta.pk)
            reprocessados.append(alerta.pk)
        return Response({"mensagem": f"{len(reprocessados)} alertas reprocessados", "ids": reprocessados})


class FinanceiroResumoViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=["get"])
    def resumo(self, request):
        # total de mensalidades
        total_mensalidade = Mensalidade.objects.count()
        total_mensalidade_pagas = Mensalidade.objects.pagas().count()
        total_mensalidade_pendentes = Mensalidade.objects.pendentes().count()
        total_mensalidade_atrasadas = Mensalidade.objects.atrasadas().count()

        # Totais de pagamentos
        total_pagamento = Pagamento.objects.count()
        valor_recebido = sum(p.valor for p in Pagamento.objects.all())

        # Totais de salários
        total_salarios = Salario.objects.count()
        salarios_pagos = Salario.objects.pagos().count()
        salarios_pendentes = Salario.objects.pendentes().count()

        # Totais de faturas
        total_faturas = Fatura.objects.count()
        faturas_pagas = Fatura.objects.pagas().count()
        faturas_vencidas = Fatura.objects.vencidas().count()

        return Response({
            "mensalidade": {
                "total": total_mensalidade,
                "pagas": total_mensalidade_pagas,
                "pendentes": total_mensalidade_pendentes,
                "atrasadas": total_mensalidade_atrasadas,
            },
            "pagamento": {
                "total": total_pagamento,
                "valor_recebido": valor_recebido,
            },
            "salarios": {
                "total": total_salarios,
                "pagos": salarios_pagos,
                "pendentes": salarios_pendentes,
            },
            "fatura": {
                "total": total_faturas,
                "pagas": faturas_pagas,
                "vencidas": faturas_vencidas,
            }
        })
