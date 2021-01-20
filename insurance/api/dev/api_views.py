from rest_framework import generics, permissions, status
from rest_framework.response import Response

from insurance.insurance_calc import calc_insurance
from insurance.haushaltsversicherung_extra.haushaltsversicherung_calc import do_calculate as calc_wse
from insurance.vav_exklusiv.haushaltsversicherung_calc import do_calculate as calc_vav

from .serializers import InsuranceCalculateSerializer


class CalculateInsurance(generics.GenericAPIView):
    serializer_class = InsuranceCalculateSerializer
    permission_classes = [permissions.AllowAny]

    # POST data needed for a specific insurance type and return prices
    def post(self, request, *args, **kwargs):
        submit_serializer = InsuranceCalculateSerializer(data=request.data)

        data = submit_serializer.validate(data=request.data)

        vav_dict = calc_insurance('vav_exklusiv/haushaltsversicherung_vars.json',
                                  'vav_exklusiv/haushaltsversicherung_fields.json',
                                  'vav_exklusiv/haushaltsversicherung_meta.json',
                                  calc_vav,
                                  data)

        wse_dict = calc_insurance('haushaltsversicherung_extra/haushaltsversicherung_vars.json',
                                  'haushaltsversicherung_extra/haushaltsversicherung_fields.json',
                                  'haushaltsversicherung_extra/haushaltsversicherung_meta.json',
                                  calc_wse,
                                  data)

        overview_list = []
        overview_list.append(data)
        overview_list.append(vav_dict)
        overview_list.append(wse_dict)

        return Response(overview_list, status=status.HTTP_200_OK)
