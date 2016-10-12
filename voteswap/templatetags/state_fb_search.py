from django import template
import us

register = template.Library()

state_fb_ids = {
    'Alabama': '104037882965264',
    'Alaska': '108083605879747',
    'Arizona': '108296539194138',
    'Arkansas': '111689148842696',
    'California': '108131585873862',
    'Colorado': '106153826081984',
    'Connecticut': '112750485405808',
    'Delaware': '105643859470062',
    'District Of Columbia': '110184922344060',
    'Florida': '109714185714936',
    'Georgia': '103994709636969',
    'Hawaii': '113667228643818',
    'Idaho': '108037302558105',
    'Illinois': '112386318775352',
    'Indiana': '111957282154793',
    'Iowa': '104004246303834',
    'Kansas': '105493439483468',
    'Kentucky': '109438335740656',
    'Louisiana': '112822538733611',
    'Maine': '108603925831326',
    'Maryland': '108178019209812',
    'Massachusetts': '112439102104396',
    'Michigan': '109706309047793',
    'Minnesota': '112577505420980',
    'Mississippi': '113067432040067',
    'Missouri': '103118929728297',
    'Montana': '109983559020167',
    'Nebraska': '109306932420886',
    'Nevada': '109176885767113',
    'New Hampshire': '105486989486087',
    'New Jersey': '108325505857259',
    'New Mexico': '108301835856691',
    'New York': '112825018731802',
    'North Carolina': '104083326294266',
    'North Dakota': '104131666289619',
    'Ohio': '104024609634842',
    'Oklahoma': '105818976117390',
    'Oregon': '109564342404151',
    'Pennsylvania': '105528489480786',
    'Rhode Island': '108295552526163',
    'South Carolina': '108635949160808',
    'South Dakota': '112283278784694',
    'Tennessee': '108545005836236',
    'Texas': '108337852519784',
    'Utah': '104164412953145',
    'Vermont': '107907135897622',
    'Virginia': '109564639069465',
    'Washington': '110453875642908',
    'West Virginia': '112083625475436',
    'Wisconsin': '109146809103536',
    'Wyoming': '104039182964473',
}


@register.filter
def fb_link(state_name):
    fb_id = state_fb_ids[us.states.lookup(unicode(state_name)).name.title()]
    return (
        "https://www.facebook.com/search/{id}/residents/present/me/friends/"
        "intersect").format(id=fb_id)
