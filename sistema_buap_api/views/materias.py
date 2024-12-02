from django.shortcuts import render, get_object_or_404
from django.db.models import *
from django.db import transaction
from sistema_buap_api.serializers import *
from sistema_buap_api.models import *
from rest_framework import permissions, generics, status
from rest_framework.response import Response
import json

class MateriasAll(generics.CreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    def get(self, request, *args, **kwargs):
        materias = Materias.objects.all().order_by("id")
        materias = MateriaSerializer(materias, many=True).data
        if not materias:
            return Response({}, 400)
        for materia in materias:
            materia["dias_json"] = json.loads(materia["dias_json"]) if materia["dias_json"] else []
        return Response(materias, 200)

class MateriaView(generics.CreateAPIView):
    def get(self, request, *args, **kwargs):
        materia = get_object_or_404(Materias, id=request.GET.get("id"))
        materia = MateriaSerializer(materia, many=False).data
        materia["dias_json"] = json.loads(materia["dias_json"]) if materia["dias_json"] else []
        return Response(materia, 200)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        try:
            # Validar si existe el NRC
            if Materias.objects.filter(nrc=request.data.get("nrc")).exists():
                return Response({"message": f"El NRC {request.data.get('nrc')} ya está registrado"}, 400)

            # Obtener el profesor
            profesor = get_object_or_404(Maestros, id=request.data.get("profesor_id"))

            # Procesar dias_json solo si viene de form-data
            dias_json = request.data.get("dias_json", [])
            content_type = request.content_type or ''
            
            if 'form' in content_type.lower() and isinstance(dias_json, str):
                # Solo procesar si viene de form-data y es string
                try:
                    dias_json = json.loads(dias_json)
                except json.JSONDecodeError:
                    pass

            # Crear materia
            materia = Materias.objects.create(
                nrc=request.data.get("nrc"),
                nombre=request.data.get("nombre"),
                seccion=request.data.get("seccion"),
                dias_json=json.dumps(dias_json),
                hora_inicio=request.data.get("hora_inicio"),
                hora_fin=request.data.get("hora_fin"),
                salon=request.data.get("salon"),
                programa_educativo=request.data.get("programa_educativo"),
                profesor=profesor,
                creditos=request.data.get("creditos")
            )
            materia.save()

            return Response({"materia_created_id": materia.id}, 201)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class MateriasViewEdit(generics.CreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    
    def put(self, request, *args, **kwargs):
        materia = get_object_or_404(Materias, id=request.data["id"])
        
        # Verificar NRC único excluyendo la materia actual
        if request.data.get("nrc") and Materias.objects.filter(nrc=request.data["nrc"]).exclude(id=materia.id).exists():
            return Response({"message": f"El NRC {request.data.get('nrc')} ya está registrado"}, 400)

        # Obtener profesor si se proporciona
        if "profesor_id" in request.data:
            profesor = get_object_or_404(Maestros, id=request.data["profesor_id"])
            materia.profesor = profesor

        materia.nrc = request.data.get("nrc", materia.nrc)
        materia.nombre = request.data.get("nombre", materia.nombre)
        materia.seccion = request.data.get("seccion", materia.seccion)
        if "dias_json" in request.data:
            materia.dias_json = json.dumps(request.data["dias_json"])
        materia.hora_inicio = request.data.get("hora_inicio", materia.hora_inicio)
        materia.hora_fin = request.data.get("hora_fin", materia.hora_fin)
        materia.salon = request.data.get("salon", materia.salon)
        materia.programa_educativo = request.data.get("programa_educativo", materia.programa_educativo)
        materia.creditos = request.data.get("creditos", materia.creditos)
        materia.save()

        serialized_materia = MateriaSerializer(materia, many=False).data
        serialized_materia["dias_json"] = json.loads(serialized_materia["dias_json"]) if serialized_materia["dias_json"] else []
        return Response(serialized_materia, 200)
    
    def delete(self, request, *args, **kwargs):
        materia = get_object_or_404(Materias, id=request.GET.get("id"))
        try:
            materia.delete()
            return Response({"details": "Materia eliminada"}, 200)
        except Exception as e:
            return Response({"details": "Algo pasó al eliminar", "error": str(e)}, 400)