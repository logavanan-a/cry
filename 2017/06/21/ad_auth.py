import ldap

#function to authenticate AD user
def auth_ad_user(username,password):
    ldap_server = "ldap://192.168.1.57"
    ldap_client = ldap.initialize(ldap_server)
    ldap_client.set_option(ldap.OPT_REFERRALS,0)
    try:
        ldap_client.simple_bind_s(username,password)
        return 1
    except:
        return 0

#Function to get MEAL group users
def get_ad_user():
    ldap_server = "ldap://192.168.1.57"
    ldap_client = ldap.initialize(ldap_server)
    ldap_client.set_option(ldap.OPT_REFERRALS,0)
    try:
        ldap_client.simple_bind_s('administrator@blrcry.com','Google098!')
    except:
        return 0
    usr = ldap_client.search_s("DC=blrcry,DC=com",ldap.SCOPE_SUBTREE,"(&(&(objectCategory=person)(objectClass=user))(memberOf=cn=MEAL,OU=SSO,OU=All India Security Groups,OU=All Locations,DC=blrcry,DC=com))",['userPrincipalName','givenName'])
    ad_user = []
    for us in usr:
        if type(us[1]) == dict:
            one_user = {}
            one_user['user']=us[1]['givenName'][0]
            one_user['email']=us[1]['userPrincipalName'][0]
            ad_user.append(one_user)
    group = ldap_client.search_s("DC=blrcry,DC=com",ldap.SCOPE_SUBTREE,"(&(&(objectCategory=group)(objectClass=group))(memberOf=cn=MEAL,OU=SSO,OU=All India Security Groups,OU=All Locations,DC=blrcry,DC=com))")
    #print group
    for grp in group:
        if grp[0] != None:
            cn = grp[0].split(",")[0]
            grp_members = []
#            try:
#                grp_members = ldap_client.search_s(grp[0],ldap.SCOPE_SUBTREE,"(objectCategory=group)",['member'])
#                try:
#                    for gr_mem in grp_members:
#                        print gr_mem[1]['member']
#                        for one in gr_mem[1]['member']:
#                            try:
#                                grp_one_mem = ldap_client.search_s(one,ldap.SCOPE_SUBTREE,"(objectCategory=user)",['userPrincipalName','givenName'])
#                                ad_user.append({'user':grp_one_mem[0][1]['givenName'][0],'email':grp_one_mem[0][1]['userPrincipalName'][0]})
#                            except:
#                                print one
#                except:
#                    print grp[0]
#            except:
#                print grp[0]
            ad_user.extend(get_group_members(grp[0],[]))
    # eliminate duplicate users and return the unique list
    return [dict(t) for t in set([tuple(d.items()) for d in ad_user])]

def get_group_members(path,ad_user=[]):
    ldap_server = "ldap://192.168.1.57"
    ldap_client = ldap.initialize(ldap_server)
    ldap_client.set_option(ldap.OPT_REFERRALS,0)
    try:
        ldap_client.simple_bind_s('administrator@blrcry.com','Google098!')
    except:
        return 0
    #print " group ",path
    grp_members = ldap_client.search_s(path,ldap.SCOPE_SUBTREE,"(objectCategory=group)",['member'])
    ad_user = ad_user
    
    for gr_mem in grp_members:
        try:
            for one in gr_mem[1]['member']:
                try:
                    grp_one_mem = ldap_client.search_s(one,ldap.SCOPE_SUBTREE,"(objectCategory=user)",['userPrincipalName','givenName'])
                    ad_user.append({'user':grp_one_mem[0][1]['givenName'][0],'email':grp_one_mem[0][1]['userPrincipalName'][0]})
                    #print {'user':grp_one_mem[0][1]['givenName'][0],'email':grp_one_mem[0][1]['userPrincipalName'][0]}
                except:
                    #print " sub group ",one
                    get_group_members(one,ad_user)
        except:
            #print " group member ",gr_mem
            return 0
    return ad_user
