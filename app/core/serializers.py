from rest_framework import serializers
from core.models import User, Cargo, Aluno, Encarregado, Motorista


class CargoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cargo
        fields = ["id", "nome", "salario_padrao"]


class UserSerializer(serializers.ModelSerializer):
    perfil_aluno = serializers.PrimaryKeyRelatedField(read_only=True)
    perfil_encarregado = serializers.PrimaryKeyRelatedField(read_only=True)
    perfil_motorista = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = User
        fields = ("id", "email", "nome", "role", "salario", "password", "perfil_aluno", "perfil_encarregado", "perfil_motorista")
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class EncarregadoSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Encarregado
        fields = ("id", "user", "foto", "telefone", "nrBI", "endereco", "ativo")

    def create(self, validated_data):
        user_data = validated_data.pop("user")
        user_serializer = UserSerializer(data=user_data)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()
        return Encarregado.objects.create(user=user, **validated_data)

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", None)
        if user_data:
            user_serializer = UserSerializer(instance.user, data=user_data, partial=True)
            user_serializer.is_valid(raise_exception=True)
            user_serializer.save()
        return super().update(instance, validated_data)


class AlunoSerializer(serializers.ModelSerializer):
    idade = serializers.IntegerField(read_only=True)

    class Meta:
        model = Aluno
        fields = ("id", "user", "foto", "idade", "data_nascimento", "escola_dest", "classe", "mensalidade", "ativo", "encarregado")
        read_only_fields = ("encarregado",)


class MotoristaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Motorista
        fields = ("id", "user", "foto", "data_nascimento", "nrBI", "carta_conducao", "telefone", "endereco", "ativo")
