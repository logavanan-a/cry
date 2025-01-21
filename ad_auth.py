import ldap
from ccd.settings import LDAP_URL
from userroles.models import UserRoles

#function to authenticate AD user
def auth_ad_user(adtable_user,password):
    ldap_server = LDAP_URL
    ldap_client = ldap.initialize(ldap_server)
    ldap_client.set_option(ldap.OPT_REFERRALS,0)
    user = adtable_user.user
    try:
        if not user.is_superuser:
            user_partner_activated = UserRoles.objects.get(user = user)
            if user_partner_activated.partner is not None:
                if user_partner_activated.partner.active != 2:
                    return 0
        ldap_client.simple_bind_s(adtable_user.email,password)
        return 1
    except Exception as e:
        return 0

#Function to get MEAL group users
def get_ad_user():
    ldap_server = LDAP_URL
    ldap_client = ldap.initialize(ldap_server)
    ldap_client.set_option(ldap.OPT_REFERRALS,0)
    try:
        ldap_client.simple_bind_s('administrator@blrcry.com','Google098!')
    except:
        return 0
    usr = ldap_client.search_s("DC=cry,DC=in",ldap.SCOPE_SUBTREE,"(&(&(objectCategory=person)(objectClass=user))(memberOf=cn=MEAL,OU=SSO,OU=All India Security Groups,OU=All Locations,DC=cry,DC=in))",['userPrincipalName','givenName','sAMAccountName'])
    ad_user = []
    for us in usr:
        if type(us[1]) == dict:
            one_user = {}
            one_user['user']=us[1]['sAMAccountName'][0]
            one_user['email']=us[1]['userPrincipalName'][0]
            one_user['firstName']=us[1]['givenName'][0]
            ad_user.append(one_user)
    group = ldap_client.search_s("DC=cry,DC=in",ldap.SCOPE_SUBTREE,"(&(&(objectCategory=group)(objectClass=group))(memberOf=cn=MEAL,OU=SSO,OU=All India Security Groups,OU=All Locations,DC=cry,DC=in))")
    for grp in group:
        if grp[0] != None:
            ad_user.extend(get_group_members(grp[0],[]))
    # eliminate duplicate users and return the unique list
    return [dict(t) for t in set([tuple(d.items()) for d in ad_user])]

def get_group_members(path,ad_user=[]):
    ldap_server = LDAP_URL
    ldap_client = ldap.initialize(ldap_server)
    ldap_client.set_option(ldap.OPT_REFERRALS,0)
    try:
        ldap_client.simple_bind_s('administrator@blrcry.com','Google098!')
    except:
        return 0
    grp_members = ldap_client.search_s(path,ldap.SCOPE_SUBTREE,"(objectCategory=group)",['member'])
    for gr_mem in grp_members:
        try:
            for one in gr_mem[1]['member']:
                try:
                    grp_one_mem = ldap_client.search_s(one,ldap.SCOPE_SUBTREE,"(objectCategory=user)",['userPrincipalName','givenName','sAMAccountName'])
                    ad_user.append({'user':grp_one_mem[0][1]['sAMAccountName'][0],'email':grp_one_mem[0][1]['userPrincipalName'][0],'firstName':grp_one_mem[0][1]['givenName'][0]})
                except:
                    get_group_members(one,ad_user)
        except:
            pass
    return ad_user
