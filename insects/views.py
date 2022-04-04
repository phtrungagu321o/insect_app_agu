import datetime
import magic
import pandas as pd
import xlwt
import xlrd
# from folium import folium
# from folium import folium
from django.core.files.storage import default_storage
from app import settings
from .import_excel import import_excel_handler
from django.shortcuts import render
from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from .models import Insect, Insect_Image, Rect, staticURL, save_img_to, Kingdom, Phylum, Classes, Order, Family, Genus, \
    Insect_downloadFile, FilesAdmin
from . import models
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from . import forms
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import Test
from django.shortcuts import get_object_or_404
import random
import os
from django.core import serializers
import json
from pathlib import Path
import numpy as np
import folium
# import pandas as pd
# import matplotlib.pyplot as plt
from .view_Handler import ViewHandler
from .crawler import Crawler
import torch

viewHandler = ViewHandler()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def insect_slug(request, slug):
    # insect = Insect.objects.get(slug=slug)
    return HttpResponse(slug)


def getInsectImage(request):
    args = viewHandler.getInsectImage(random=False, insect=request.POST["slug"], index=request.POST["index"])
    print(args)
    return HttpResponse(json.dumps(viewHandler.ConvertToJson(args)))


def home(request):
    args = viewHandler.getInsectImage()
    return render(request, 'insect/home.html', args)


def image(request, image):
    image_data = open(
        "images/validation/Ant/" + image, "rb").read()
    response = HttpResponse(image_data, content_type='image')
    return response


def getAllInsect(request):
    insect = Insect.objects.all()
    data = serializers.serialize('json', insect)
    return HttpResponse(data)


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if 'next' in request.POST:
                return redirect(request.POST.get('next'))
            else:
                if user.is_staff == True:
                    return redirect('/admin')
                else:
                    return redirect('insects:home')
    else:
        form = AuthenticationForm()
    return render(request, 'insect/login.html', {'form': form})


def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('insects:home')
    else:
        form = UserCreationForm()
    return render(request, 'insect/register.html', {'UserCreationForm': form})


def getAllUser(request):
    user = User.objects.all()
    data = serializers.serialize('json', user)
    return HttpResponse(data)


def logout_view(request):
    logout(request)
    return redirect('insects:home')


@login_required(login_url='insects:login')
def import_data_view(request):
    if request.user.is_superuser == False:
        return redirect('insects:home')
    if request.method == 'GET':
        if request.user.is_staff:
            return render(request, 'insect/import_data2.html')
        else:
            return redirect('insects:home')
    else:
        result = viewHandler.ImportData(request)
        return HttpResponse(result)


def search_tool(request):
    # Kingdom, Phylum, Classes, Order, Family, Genus
    return render(request, 'insect/search_tool.html')


def detail_insect_view(request, name):
    insect = get_object_or_404(Insect, slug=name)
    # args = {}
    args = viewHandler.getInsectImage(random=False, insect=name)
    args["insect"] = insect
    try:
        args["download_url"] = Insect_downloadFile.objects.filter(insect=insect)[0]
    except:
        args["download_url"] = ""
    # insect = serializers.serialize('json', [insect])
    return render(request, 'insect/detail.html', args)


def get_taxonomy_tree(request):
    data = viewHandler.TaxonomyTree()
    return HttpResponse(data)


def ClassificationInsect(request):
    if request.method == "POST":
        data = viewHandler.Classification(request)
    else:
        data = '{"response_text": "you need post method"}'
    return HttpResponse(data)


def getfiles(request, insect_slug):
    # Files (local path) to put in the .zip
    # FIXME: Change this (get paths from DB etc)

    response = viewHandler.Compress(insect_slug)
    return response


crawler = Crawler()
from threading import Thread
import threading


def crawl_image(request):
    if request.method != "POST":
        return render(request, "insect/crawl.html")

    result = {}
    if viewHandler.threading == True:
        result["message"] = "t1 is already exist"
        return HttpResponse(json.dumps(result))

    crawl_name = request.POST["crawl_input"]
    print(crawl_name)
    crawler.img_urls = []
    t1 = threading.Thread(target=viewHandler.CrawlImage, args=(crawl_name, crawler, int(request.POST["count"])))
    t1.start()
    viewHandler.threading = True
    print("thread starting")
    # result = viewHandler.CrawlImage(slug=crawl_name, crawler=crawler, limit=1)
    # if result == {}:
    #     return HttpResponse('{"message": "Insect not found"}')

    result["message"] = "thread is tarted"
    return HttpResponse(json.dumps(result))


def get_current_urls(request):
    result = {}
    result["urls"] = crawler.img_urls
    return HttpResponse(json.dumps(result))


def compare_url_image(request):
    insect = models.Insect.objects.filter(slug=viewHandler.slug)
    imgs = models.Insect_Image.objects.filter(insect=insect[0])

    result = viewHandler.CompareByUrl(request.POST["image"], imgs)
    print(result)
    return HttpResponse(json.dumps(result))


@login_required(login_url='insects:login')
def import_new(request):
    if request.user.is_superuser == False:
        return redirect('insects:home')
    if request.method == 'GET':
        if request.user.is_staff:
            return render(request, 'insect/import_new.html')
        else:
            return redirect('insects:home')
    else:
        result = viewHandler.ImportNew(request)
        return HttpResponse(result)


@login_required(login_url='insects:login')
def export_excel(request):
    response = HttpResponse(content_type="application/ms-excel")
    response["Content-Disposition"] = "attachment; filename=Expenses" + \
                                      str(datetime.datetime.now()) + ".xls"

    wb = xlwt.Workbook(encoding="utf-8")
    ws = wb.add_sheet("Expenses")
    row_num = 0
    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    columns = ["Genus", "Ename", "Name", "Slug", "Characteristic", "Value", "Reality", "Protective", "Distribution",
               "Detail"]

    for col in range(len(columns)):
        ws.write(row_num, col, columns[col], font_style)

    font_style = xlwt.XFStyle()

    rows = Insect.objects.all()

    for row in rows:
        row_num += 1
        ws.write(row_num, 0, str(row.genus.eName), font_style)
        ws.write(row_num, 1, str(row.eName), font_style)
        ws.write(row_num, 2, str(row.name), font_style)
        ws.write(row_num, 3, str(row.slug), font_style)
        ws.write(row_num, 4, str(row.characteristic), font_style)
        ws.write(row_num, 5, str(row.value), font_style)
        ws.write(row_num, 6, str(row.reality), font_style)
        ws.write(row_num, 7, str(row.protective), font_style)
        ws.write(row_num, 8, str(row.distribution), font_style)
        ws.write(row_num, 9, str(row.detail), font_style)

    wb.save(response)
    return response


@login_required(login_url='insects:login')
def import_excel(request):
    if (request.method == "POST"):
        tmp = import_excel_handler(request.FILES['input_excel'])
        # for rx in range(sh.nrows):
        #     for cx in range(sh.ncols):
        #         output += str(sh.cell_value(rowx=rx, colx=cx)) + "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"

        #     output += "<br/>"
        if tmp.status == False:
            return HttpResponse("False")

        tmp.Import()
        return HttpResponse(tmp.warningMessage)
    else:
        return render(request, "insect/import_excel.html")


@login_required(login_url='insects:login')
def upload_new_image(request):
    if viewHandler.UploadNewImage(request=request):
        return HttpResponse('{"result" : "done"}')

    return HttpResponse('{"result": "false"}')


@login_required(login_url='insects:login')
def DownloadImageFromUrl(request):
    if viewHandler.DownloadImageFromUrl(request=request):
        return HttpResponse('{"result" : "done"}')

    return HttpResponse('{"result": "false"}')


@login_required(login_url='insects:login')
def getNewImageToDraw(request):
    if request.method == "GET":
        return redirect('insects:home')
    if request.user.is_staff == False:
        return redirect('insects:home')

    if int(request.POST["index"]) < 0:
        data = {}
        data["res"] = False
    insect = models.Insect.objects.get(slug=request.POST["insect"])

    if insect is None:
        data = {}
        data["result"] = False

    try:
        newImg = models.New_Image.objects.filter(insect=insect, is_valid=False)[int(request.POST['index'])]

        print(serializers.serialize('json', [newImg]))
        data = serializers.serialize('json', [newImg])
    except:
        data = {}
        data["result"] = False

    return HttpResponse(data)


@login_required(login_url='insects:login')
def getNewImgRect(request):
    if request.method == "GET":
        return redirect('insects:home')
    if request.user.is_staff == False:
        return redirect('insects:home')

    insect = models.Insect.objects.get(slug=request.POST["insect"])
    newImg = models.New_Image.objects.filter(insect=insect, is_valid=False)[int(request.POST['index'])]
    rects = models.Rect_New_Image.objects.filter(image=newImg)
    data = serializers.serialize('json', rects)

    return HttpResponse(data)


@login_required(login_url='insects:login')
def saveRectNewImg(request):
    if request.method == "GET":
        return redirect('insects:home')
    if request.user.is_staff == False:
        return redirect('insects:home')

    rects = request.POST["rects"]
    rects = json.loads(rects)
    print(len(rects))
    insect = models.Insect.objects.get(slug=request.POST["insect"])
    newImg = models.New_Image.objects.filter(insect=insect, is_valid=False)[int(request.POST['index'])]
    newImg.is_valid = True
    newImg.save()
    print(serializers.serialize('json', [newImg]))
    data = viewHandler.YoloToPascalVOC(rects, newImg.image)
    for i in range(len(data)):
        newrect = models.Rect_New_Image(image=newImg, name=insect.slug, x=data[i][0], y=data[i][1], width=data[i][2],
                                        height=data[i][3])
        newrect.save()
    return HttpResponse(data)


@login_required(login_url='insects:login')
def draw_bbox(request):
    if request.user.is_staff == False:
        return redirect('insects:home')
    ni = models.New_Image.objects.filter(is_valid=False).values_list('insect')
    insect = models.Insect.objects.filter(pk__in=ni)
    return render(request, "insect/draw_bbox.html", {"insects": insect})


@login_required(login_url='insects:login')
def getNewImg(request):
    if request.user.is_staff == False:
        return redirect('insects:home')

    newimg = models.New_Image.objects.all()
    data = serializers.serialize('json', [newimg])
    return HttpResponse(data)


@login_required(login_url='insects:login')
def autoBBox(request):
    if request.user.is_staff == False:
        return redirect('insects:home')
    viewHandler.CreateBBox(request)
    return HttpResponse("x")


def index_map(request):
    m = folium.Map(location=[19, -12], tiles="Stamen Terrain",width=1000,zoom_start=2)
    df=pd.read_csv('data.csv')

    for i, row in df.iterrows():
        lat =df.at[i, 'lat']
        lng= df.at[i, 'lng']
        name=df.at[i,'name']
        html = f"""
               <h1> {name}</h1>
              """

        if name =='Cnaphalocrocis_medinalis':
            color='blue'
        if name =='Chlorops_oryzae':
            color='green'
        if name == 'Chilo_suppressalis':
            color = 'black'
        if name == 'Scirpophaga_incertulas':
            color = 'red'
        if name == 'Orseolia_oryzae':
            color = 'gray'
        if name == 'Pachydiplosis_oryzae':
            color = 'orange'
        if name == 'Nilaparvata_lugens':
            color = 'pink'
        if name == 'Sogata_furcifera':
            color = 'purple'
        if name == 'Laodelphax_striatellus':
            color = 'yellow'
        if name == 'Lissorhoptrus_oryzophilus_Kuschel':
            color = 'white'
        # if name == 'Nilaparvata lugens':
        #     color = 'yellow'

        folium.Marker(
                location=[lat, lng],
                popup=html,
                icon=folium.Icon(color=color),
            ).add_to(m)

    m = m._repr_html_()
    context = {
        'm': m,
    }
    if request.method == "POST":
        searched = request.POST['searched']
        m = folium.Map(location=[19, -12],tiles="Stamen Terrain",width=1000, zoom_start=2)
        for i, row in df.iterrows():
            lat = df.at[i, 'lat']
            lng = df.at[i, 'lng']
            name1 = df.at[i, 'name']

            if name1 == searched:
                folium.Marker(
                    location=[lat, lng],
                    popup=name1,
                    icon=folium.Icon(color='red'),
                ).add_to(m)
        m = m._repr_html_()
        context = {
            'm': m,
        }
        return render(request, 'insect/map.html', {'searched': searched , 'm':m})
    else:
        return render(request, "insect/map.html",{'m':m })

def index_map1(request):

    df=pd.read_csv('data.csv')
        # searched = request.POST['searched']
    m = folium.Map(location=[19, -12],tiles="Stamen Terrain",width=1000, zoom_start=2)

    for i, row in df.iterrows():
            lat = df.at[i, 'lat']
            lng = df.at[i, 'lng']
            name1 = df.at[i, 'name']

            if name1 == "Chlorops_oryzae":
                folium.Marker(
                        location=[lat, lng],
                        popup=f"""
                           <h1> insect_{name1}</h1>
                          """,
                        icon=folium.Icon(color='red'),
                ).add_to(m)
    m = m._repr_html_()
    context = {
            'm': m,
        }
    return render(request, 'insect/map.html', {'m':m})

def download_home(request):
    context = {'file': FilesAdmin.objects.all()}
    return render(request, 'insect/download.html', context)


def download(request, path):
    file_path = os.path.join(settings.MEDIA_ROOT, path)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="applicaton/adminupload")
            response['Content-Disposition'] = 'inline;filename=' + os.path.basename(file_path)
            return response
    return Http404


def search_insect(request):
    if request.method == "POST":
        searched = request.POST['searched']
        insects = FilesAdmin.objects.filter(title__contains=searched)
        return render(request, 'insect/download.html', {'searched': searched, 'insects': insects})
    else:
        return render(request, 'insect/download.html')
    # Kingdom, Phylum, Classes, Order, Family, Genus


def search_img(request):
    if request.method == 'POST':

        file = request.FILES["imageFile"]
        # print(file)
        file_names = default_storage.save(file.name, file)
        file_url = default_storage.path(file_names)
        # print(file_url)

        model = torch.hub.load('ultralytics/yolov5', 'custom', path='best.pt')

        results = model(file_url, size=640)

        result = results.pandas().xyxy[0].to_json(orient='records')

        parsed = json.loads(result)
        # print(parsed)

        try:
            classNum = int(parsed[0]['class'])

            # print(classNum)

            def detection(x):
                switcher = {
                    0: 'Cnaphalocrocis_medinalis',
                    1: 'Cnaphalocrocis_medinalis',
                    2: 'Chlorops_oryzae',
                    3: 'Chilo_suppressalis',
                    4: 'Scirpophaga_incertulas',
                    5: 'Orseolia_oryzae',
                    6: 'Pachydiplosis_oryzae',
                    7: 'Nilaparvata_lugens',
                    8: 'Sogata_furcifera',
                    9: 'Laodelphax_striatellus',
                    10: 'Lissorhoptrus_oryzophilus_Kuschel',
                    11: 'Nilaparvata_lugens',
                    12: 'Stenchaetothrips_biformis',
                    13: 'Gryllotalpa_brachyptera',
                    14: 'Varies',
                    15: 'mole_cricket',
                    16: 'Melanotus_spp',
                    17: 'Pieris_Brassicae',
                    18: 'Agrotis_ipsilon',
                    19: 'Noctua_pronuba',
                    20: 'Large_yellow_underwing',
                    21: 'Tetranychus_sp',
                    22: 'Ostrinia_nubilalis_Huber',
                    23: 'Fall_armyworm',
                    24: 'Aphidoidea',
                    25: 'Ground_Beetles',
                    26: 'Synanthedon_exitiosa',
                    27: 'Sitobion_avenae',
                    28: 'Green_stink_bug',
                    29: 'Rhopalosiphum_padi',
                    30: 'Sitodiplosis_mosellana',
                    31: 'Penthaleus_major',
                    32: 'Spider_mite',
                    33: 'Haplothrips_aculeatus',
                    34: 'Wheat_Stem_Sawfly',
                    35: 'Agromyzidae',
                    36: 'Pegomya_hyoscyami',
                    37: 'Flea_beetle',
                    38: 'Spodoptera_eridania',
                    39: 'Beet_armyworm',
                    40: 'Tetanops_myopaeformis',
                    41: 'Loxostege_sticticalis',
                    42: 'Tanymecus_palliatus',
                    43: 'Phaeochrous_emarginatus',
                    44: 'Hypera_postica',
                    45: 'Heliothis_virescens',
                    46: 'Adelphocoris_lineolatus',
                    47: 'Tarnished_plant_bug',
                    48: 'Grasshopper',
                    49: 'lytta_polita',
                    50: 'Ceroctis_capensis',
                    51: 'blister_beetle',
                    52: 'Therioaphis_trifolii',
                    53: 'odontothrips_loti',
                    54: 'Stenchaetothrips_biformis',
                    55: 'Bruchophagus_roddi',
                    56: 'Pieris_canidia',
                    57: 'Apolygus_lucorum',
                    58: 'Limacodidae',
                    59: 'Viteus_vitifoliae',
                    60: 'Eriophyes_vitis',
                    61: 'Brevipalpus_lewisi',
                    62: 'oides_decempunctata',
                    63: 'Polyphagotarsonemus_latus',
                    64: 'Pseudococcus_comstocki',
                    65: 'Paranthrene_tabaniformis',
                    66: 'Ampelophaga_rubiginosa',
                    67: 'Spotted_lanternfly',
                    68: 'Xylotrechus_quadripes',
                    69: 'Cicadella_viridis',
                    70: 'Miridae',
                    71: 'Trialeurodes_vaporariorum',
                    72: 'Erythroneura_apicalis',
                    73: 'Papilio_xuthus',
                    74: 'Panonchus_citri_McGregor',
                    75: 'Phyllocoptes_oleiverus_ashmead',
                    76: 'Icerya_purchasi_Maskell',
                    77: 'Unaspis_yanonensis',
                    78: 'Ceroplastes_rubens',
                    79: 'Chrysomphalus_aonidum',
                    80: 'Parlatoria_zizyphus_Lucus',
                    81: 'Nipaecoccus_vastalor',
                    82: 'Aleurocanthus_spiniferus',
                    83: 'Tetradacus_c_Bactrocera_minax',
                    84: 'Bactrocera_dorsalis',
                    85: 'Bactrocera_tsuneonis',
                    86: 'Spodoptera_litura',
                    87: 'Adris_tyrannus',
                    88: 'Phyllocnistis_citrella_Stainton',
                    89: 'Toxoptera_citricidus',
                    90: 'Toxoptera_aurantii',
                    91: 'Aphis_citricola_van_der_Goot',
                    92: 'Scirtothrips_dorsalis',
                    93: 'Dasineura_sp_near_capsulae',
                    94: 'Lawana_imitata',
                    95: 'Green_moth_wax_cicada',
                    96: 'Deporaus_marginatus',
                    97: 'Hofmannophila_pseudospretella',
                    98: 'Idioscopus_nitidulus',
                    99: 'Cerambycinae',
                    100: 'Sternochetus_frigidus',
                    101: 'Cicadellidae'
                }
                return switcher.get(x, "nothing")


            name_sce = detection(classNum)

            label = parsed[0]['name']
            path_save = str('assets/img/exp/' + label)
            results.save(path_save)
            path_save1 = str('img/exp/' + label + '/' + file_names)
            return render(request, 'insect/search_tool.html', {
                'ms': '',
                'path_ins': path_save1,
                'name_sc': name_sce,
            })

        except:
            return render(request, 'insect/search_tool.html', {'ms': 'Thất bại', 'path_ins': '',
                                                               'name_sc': ''})
    return render(request, 'insect/search_tool.html', {'ms': 'Thất bại', 'path_ins': '',
                                                       '.': ''})
