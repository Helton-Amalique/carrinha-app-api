from rest_framework import serializers
from core.models import User, Aluno, Encarregado, Motorista


class UserSerializer(serializers.ModelSerializer):
    perfil_aluno = serializers.PrimaryKeyRelatedField(read_only=True)
    perfil_encarregado = serializers.PrimaryKeyRelatedField(read_only=True)
    perfil_motorista = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "nome",
            "role",
            "salario",
            "password",
            "perfil_aluno",
            "perfil_encarregado",
            "perfil_motorista",
        )
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        
        # Validar role para garantir que apenas Admin pode criar outros Admins
        role = validated_data.get('role', 'ALUNO') # Default to ALUNO if not provided
        request = self.context.get('request')
        if role == 'ADMIN':
            if not request or not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser or request.user.role == 'ADMIN'):
                 # Em vez de erro, forçamos um role seguro ou lançamos erro?
                 # Lançar erro é mais seguro para não criar admin sem querer.
                 raise serializers.ValidationError({"role": "Apenas administradores podem criar usuários ADMIN."})

        # Usa o manager para garantir regras de negócio
        user = User.objects.create_user(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        
        # Validar alteração de role
        if 'role' in validated_data:
            new_role = validated_data['role']
            request = self.context.get('request')
            if new_role == 'ADMIN':
                 if not request or not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser or request.user.role == 'ADMIN'):
                     raise serializers.ValidationError({"role": "Apenas administradores podem promover usuários a ADMIN."})
        
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
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    encarregado = serializers.PrimaryKeyRelatedField(queryset=Encarregado.objects.all())

    class Meta:
        model = Aluno
        fields = (
            "id",
            "user",
            "foto",
            "idade",
            "data_nascimento",
            "nrBI",
            "escola_dest",
            "classe",
            "mensalidade",
            "ativo",
            "encarregado",
        )


class MotoristaSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Motorista
        fields = (
            "id",
            "user",
            "foto",
            "data_nascimento",
            "nrBI",
            "carta_conducao",
            "telefone",
            "endereco",
            "ativo",
        )
