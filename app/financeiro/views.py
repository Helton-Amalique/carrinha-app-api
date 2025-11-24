from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from financeiro.services import relatorio_financeiro
from financeiro.serializers import RelatorioFinanceiroSerializer


# financeiro/views.py
from rest_framework.decorators import action
from rest_framework import viewsets, permissions, decorators, response
from financeiro.tasks import enviar_alerta_email
from financeiro.models import Mensalidade, Pagamento, Salario, Fatura, AlertaEnviado, Despesa
from financeiro.serializers import (
    MensalidadeSerializer,
    PagamentoSerializer,
    SalarioSerializer,
    FaturaSerializer,
    AlertaEnviadoSerializer,
    RelatorioFinanceiroSerializer,
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
        return response.Response(MensalidadeSerializer(qs, many=True).data)

    @decorators.action(detail=False, methods=["get"])
    def atrasadas(self, request):
        qs = Mensalidade.objects.atrasadas()
        return response.Response(MensalidadeSerializer(qs, many=True).data)

    @decorators.action(detail=False, methods=["get"])
    def pagas(self, request):
        qs = Mensalidade.objects.pagas()
        return response.Response(MensalidadeSerializer(qs, many=True).data)


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
        return response.Response(SalarioSerializer(qs, many=True).data)

    @decorators.action(detail=False, methods=["get"])
    def pendentes(self, request):
        qs = Salario.objects.pendentes()
        return response.Response(SalarioSerializer(qs, many=True).data)


class FaturaViewSet(viewsets.ModelViewSet):
    queryset = Fatura.objects.all()
    serializer_class = FaturaSerializer
    permission_classes = [permissions.IsAuthenticated]

    @decorators.action(detail=False, methods=["get"])
    def vencidas(self, request):
        qs = Fatura.objects.vencidas()
        return response.Response(FaturaSerializer(qs, many=True).data)

    @decorators.action(detail=False, methods=["get"])
    def pagas(self, request):
        qs = Fatura.objects.pagas()
        return response.Response(FaturaSerializer(qs, many=True).data)

    @decorators.action(detail=False, methods=["get"])
    def pendentes(self, request):
        qs = Fatura.objects.pendentes()
        return response.Response(FaturaSerializer(qs, many=True).data)


class AlertaEnviadoViewSet(viewsets.ModelViewSet):
    queryset = AlertaEnviado.objects.all()
    serializer_class = AlertaEnviadoSerializer
    permission_classes = [permissions.IsAuthenticated]

    @decorators.action(detail=False, methods=["get"])
    def enviados(self, request):
        qs = AlertaEnviado.objects.enviados()
        return response.Response(AlertaEnviadoSerializer(qs, many=True).data)

    @decorators.action(detail=False, methods=["get"])
    def falhos(self, request):
        qs = AlertaEnviado.objects.falhos()
        return response.Response(AlertaEnviadoSerializer(qs, many=True).data)

    @decorators.action(detail=False, methods=["get"])
    def pendentes(self, request):
        qs = AlertaEnviado.objects.pendentes()
        return response.Response(AlertaEnviadoSerializer(qs, many=True).data)

    @decorators.action(detail=False, methods=["post"])
    def reprocessar(self, request):
        falhos = AlertaEnviado.objects.filter(status="FALHO NO ENVIO")
        reprocessados = []
        for alerta in falhos:
            enviar_alerta_email.delay(alerta.pk)
            reprocessados.append(alerta.pk)
        return response.Response({"mensagem": f"{len(reprocessados)} alertas reprocessados", "ids": reprocessados})


class FinanceiroResumoViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=["get"])
    def resumo(self, request):
        total_mensalidade = Mensalidade.objects.count()
        total_mensalidade_pagas = Mensalidade.objects.pagas().count()
        total_mensalidade_pendentes = Mensalidade.objects.pendentes().count()
        total_mensalidade_atrasadas = Mensalidade.objects.atrasadas().count()


        total_pagamento = Pagamento.objects.count()
        valor_recebido = sum(p.valor for p in Pagamento.objects.all())

        total_salarios = Salario.objects.count()
        salarios_pagos = Salario.objects.pagos().count()
        salarios_pendentes = Salario.objects.pendentes().count()

        total_faturas = Fatura.objects.count()
        faturas_pagas = Fatura.objects.pagas().count()
        faturas_vencidas = Fatura.objects.vencidas().count()

        total_despesas = Despesa.objects.count()
        valor_despesas = sum(d.valor for d in Despesa.objects.all())

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
            },
            "despesas": {
                "total": total_despesas,
                "valor": valor_despesas,
            }
        })


class RelatorioFinanceiroView(APIView):

    def get(self, request, *args, **kwargs):
        ano = request.query_params.get("ano")
        mes = request.query_params.get("mes")

        ano = int(ano) if ano else None
        mes = int(mes) if mes else None

        dados = relatorio_financeiro(ano=ano, mes=mes)
        serializer = RelatorioFinanceiroSerializer(dados)
        return Response(serializer.data, status=status.HTTP_200_OK)
