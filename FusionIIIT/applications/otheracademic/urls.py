from django.conf.urls import url

from . import views

app_name = 'otheracademic'

urlpatterns = [
    #UG Leave
    url(r'^$', views.otheracademic, name='otheracademic'),
    url(r'^leaveform/$', views.leaveform, name='leaveform'),

    url(r'^leave_form_submit/$', views.leave_form_submit, name='leave_form_submit'),
    url(r'^leaveApproveForm/$', views.leaveApproveForm, name='leaveApproveForm'),
    url(r'^leaveStatus/$', views.leaveStatus, name='leaveStatus'),

    url(r'^leaveStatus_Dip/$', views.leaveStatus_Dip, name='leaveStatus_Dip'),

    url(r'^approve_leave/(?P<leave_id>\d+)/$', views.approve_leave, name='approve_leave'),
    url(r'^reject_leave/(?P<leave_id>\d+)/$', views.reject_leave, name='reject_leave'),

    #PG/Mtech Leave
     url(r'^leavePG/$', views.leavePG, name='leavePG'),
    url(r'^leavePgSubmit/$', views.leavePgSubmit, name='leavePgSubmit'),
    url(r'^leaveApproveTA/$', views.leaveApproveTA, name='leaveApproveTA'),
    url(r'^approve_leave_ta(?P<leave_id>\d+)/$', views.approve_leave_ta, name='approve_leave_ta'),
    url(r'^reject_leave_ta(?P<leave_id>\d+)/$', views.reject_leave_ta, name='reject_leave_ta'),
    url(r'^leaveApproveThesis/$', views.leaveApproveThesis, name='leaveApproveThesis'),
    url(r'^approve_leave_thesis(?P<leave_id>\d+)/$', views.approve_leave_thesis, name='approve_leave_thesis'),
    url(r'^reject_leave_thesis(?P<leave_id>\d+)/$', views.reject_leave_thesis, name='reject_leave_thesis'),
    url(r'^leaveApproveHOD/$', views.leaveApproveHOD, name='leaveApproveHOD'),
    url(r'^approve_leave_hod(?P<leave_id>\d+)/$', views.approve_leave_hod, name='approve_leave_hod'),
    url(r'^reject_leave_hod(?P<leave_id>\d+)/$', views.reject_leave_hod, name='reject_leave_hod'),
    url(r'^leaveStatusPG/$', views.leaveStatusPG, name='leaveStatusPG'),
    url(r'^leaveStatusPG_Dip/$', views.leaveStatusPG_Dip, name='leaveStatusPG_Dip'),
    
    url(r'^graduateseminar/$', views.graduateseminar, name='graduateseminar'),
    url(r'^graduate_form_submit/$', views.graduate_form_submit, name='graduate_form_submit'),
    url(r'^graduate_status/$', views.graduate_status, name='graduate_status'),
    url(r'^graduateSeminarStatus_Dip/$', views.graduateSeminarStatus_Dip, name='graduateSeminarStatus_Dip'),
    url(r'^bonafide/$', views.bonafide, name='bonafide'),
    url(r'^bonafide_form_submit/$', views.bonafide_form_submit, name='bonafide_form_submit'),
    url(r'^bonafideApproveForm/$', views.bonafideApproveForm, name='bonafideApproveForm'),
    url(r'^approve_bonafide/(?P<leave_id>\d+)/$', views.approve_bonafide, name='approve_bonafide'),
    url(r'^reject_bonafide/(?P<leave_id>\d+)/$', views.reject_bonafide, name='reject_bonafide'),
    url(r'^bonafideStatus/$', views.bonafideStatus, name='bonafideStatus'),
    url(r'^upload_file/(?P<entry_id>\d+)/$', views.upload_file, name='upload_file'),
    # url(r'^assistantship/$', views.assistantship, name='assistantship'),
    url(r'^submitform/$', views.assistantship_form_submission, name='assistantship_form_submission'),
    # url(r'^approveform/$', views.assistantship_form_approval, name='assistantship_approval'),
    # url(r'^noduesverification/$', views.nodues, name='nodues'),
    url(r'^PG_page/$', views.PG_page, name='PG_page'),

     url(r'^noduesverification/$', views.nodues, name='nodues'),

      url(r'^Bank_nodues/$', views.Bank_nodues, name='Bank_nodues'),
      url(r'^BTP_nodues/$', views.BTP_nodues, name='BTP_nodues'),
      url(r'^CSE_nodues/$', views.CSE_nodues, name='CSE_nodues'),
      url(r'^Design_nodues/$', views.Design_nodues, name='Design_nodues'),
      url(r'^dsa_nodues/$', views.dsa_nodues, name='dsa_nodues'),
      url(r'^Ece_nodues/$', views.Ece_nodues, name='Ece_nodues'),
      url(r'^hostel_nodues/$', views.hostel_nodues, name='hostel_nodues'),
      url(r'^ME_nodues/$', views.ME_nodues, name='ME_nodues'),
      url(r'^library_nodues/$', views.library_nodues, name='library_nodues'),
      url(r'^mess_nodues/$', views.mess_nodues, name='mess_nodues'),
      url(r'^Physics_nodues/$', views.Physics_nodues, name='Physics_nodues'),
      url(r'^discipline_nodues/$', views.discipline_nodues, name='discipline_nodues'),

      url(r'^nodues_apply/$', views.nodues_apply, name='nodues_apply'),
      url(r'^nodues_status/$', views.nodues_status, name='nodues_status'),
      
      url(r'^update_dues_status/$', views.update_dues_status, name='update_dues_status'),
      url(r'^submit_nodues_form/$', views.submit_nodues_form, name='submit_nodues_form'),
      url(r'^nodues_apply/$', views.nodues_apply, name='nodues_apply'),


    url(r'^approve_BTP(?P<no_dues_id>\d+)/$', views.approve_BTP, name='approve_BTP'),
    url(r'^reject_BTP(?P<no_dues_id>\d+)/$', views.reject_BTP, name='reject_BTP'),

    url(r'^approve_bank(?P<no_dues_id>\d+)/$', views.approve_bank, name='approve_bank'),
    url(r'^reject_bank(?P<no_dues_id>\d+)/$', views.reject_bank, name='reject_bank'),
    
    url(r'^approve_CSE(?P<no_dues_id>\d+)/$', views.approve_CSE, name='approve_CSE'),
    url(r'^reject_CSE(?P<no_dues_id>\d+)/$', views.reject_CSE, name='reject_CSE'),

    url(r'^approve_design_project(?P<no_dues_id>\d+)/$', views.approve_design_project, name='approve_design_project'),
    url(r'^reject_design-project(?P<no_dues_id>\d+)/$', views.reject_design_project, name='reject_design_project'),

      url(r'^approve_design_studio(?P<no_dues_id>\d+)/$', views.approve_design_studio, name='approve_design_studio'),
    url(r'^reject_design_studio(?P<no_dues_id>\d+)/$', views.reject_design_studio, name='reject_design_studio'),

      url(r'^approve_icard(?P<no_dues_id>\d+)/$', views.approve_icard, name='approve_icard'),
    url(r'^reject_icard(?P<no_dues_id>\d+)/$', views.reject_icard, name='reject_icard'),

      url(r'^approve_placement(?P<no_dues_id>\d+)/$', views.approve_placement, name='approve_placement'),
    url(r'^reject_placement(?P<no_dues_id>\d+)/$', views.reject_placement, name='reject_placement'),

      url(r'^approve_account(?P<no_dues_id>\d+)/$', views.approve_account, name='approve_account'),
    url(r'^reject_account(?P<no_dues_id>\d+)/$', views.reject_account, name='reject_account'),

      url(r'^approve_alumni(?P<no_dues_id>\d+)/$', views.approve_alumni, name='approve_alumni'),
    url(r'^reject_alumni(?P<no_dues_id>\d+)/$', views.reject_alumni, name='reject_alumni'),

      url(r'^approve_gym(?P<no_dues_id>\d+)/$', views.approve_gym, name='approve_gym'),
    url(r'^reject_gym(?P<no_dues_id>\d+)/$', views.reject_gym, name='reject_gym'),

      url(r'^approve_discipline(?P<no_dues_id>\d+)/$', views.approve_discipline, name='approve_discipline'),
    url(r'^reject_discipline(?P<no_dues_id>\d+)/$', views.reject_discipline, name='reject_discipline'),

      url(r'^approve_signal(?P<no_dues_id>\d+)/$', views.approve_signal, name='approve_signal'),
    url(r'^reject_signal(?P<no_dues_id>\d+)/$', views.reject_signal, name='reject_signal'),

      url(r'^approve_vlsi(?P<no_dues_id>\d+)/$', views.approve_vlsi, name='approve_vlsi'),
    url(r'^reject_vlsi(?P<no_dues_id>\d+)/$', views.reject_vlsi, name='reject_vlsi'),

      url(r'^approve_ece(?P<no_dues_id>\d+)/$', views.approve_ece, name='approve_ece'),
    url(r'^reject_ece(?P<no_dues_id>\d+)/$', views.reject_ece, name='reject_ece'),

    url(r'^approve_hostel(?P<no_dues_id>\d+)/$', views.approve_hostel, name='approve_hostel'),
    url(r'^reject_hostel(?P<no_dues_id>\d+)/$', views.reject_hostel, name='reject_hostel'),
    
    url(r'^approve_library(?P<no_dues_id>\d+)/$', views.approve_library, name='approve_library'),
    url(r'^reject_library(?P<no_dues_id>\d+)/$', views.reject_library, name='reject_library'),

    url(r'^approve_workshop(?P<no_dues_id>\d+)/$', views.approve_workshop, name='approve_workshop'),
    url(r'^reject_workshop(?P<no_dues_id>\d+)/$', views.reject_workshop, name='reject_workshop'),

    url(r'^approve_mecha(?P<no_dues_id>\d+)/$', views.approve_mecha, name='approve_mecha'),
    url(r'^reject_mecha(?P<no_dues_id>\d+)/$', views.reject_mecha, name='reject_mecha'),

    url(r'^approve_mess(?P<no_dues_id>\d+)/$', views.approve_mess, name='approve_mess'),
    url(r'^reject_mess(?P<no_dues_id>\d+)/$', views.reject_mess, name='reject_mess'),
    
    url(r'^approve_physics(?P<no_dues_id>\d+)/$', views.approve_physics, name='approve_physics'),
    url(r'^reject_physics(?P<no_dues_id>\d+)/$', views.reject_physics, name='reject_physics'),




    url(r'^approve_BTP_not(?P<no_dues_id>\d+)/$', views.approve_BTP_not, name='approve_BTP_not'),
    url(r'^approve_bank_not(?P<no_dues_id>\d+)/$', views.approve_bank_not, name='approve_bank_not'), 
    url(r'^approve_CSE_not(?P<no_dues_id>\d+)/$', views.approve_CSE_not, name='approve_CSE_not'),
    url(r'^approve_design_project_not(?P<no_dues_id>\d+)/$', views.approve_design_project_not, name='approve_design_project_not'),
    url(r'^approve_design_studio_not(?P<no_dues_id>\d+)/$', views.approve_design_studio_not, name='approve_design_studio_not'),
    url(r'^approve_icard_not(?P<no_dues_id>\d+)/$', views.approve_icard_not, name='approve_icard_not'),
    url(r'^approve_placement_not(?P<no_dues_id>\d+)/$', views.approve_placement_not, name='approve_placement_not'),
    url(r'^approve_account_not(?P<no_dues_id>\d+)/$', views.approve_account_not, name='approve_account_not'),
    url(r'^approve_alumni_not(?P<no_dues_id>\d+)/$', views.approve_alumni_not, name='approve_alumni_not'),
    url(r'^approve_gym_not(?P<no_dues_id>\d+)/$', views.approve_gym_not, name='approve_gym_not'),
    url(r'^approve_discipline_not(?P<no_dues_id>\d+)/$', views.approve_discipline_not, name='approve_discipline_not'),
    url(r'^approve_signal_not(?P<no_dues_id>\d+)/$', views.approve_signal_not, name='approve_signal_not'),
    url(r'^approve_vlsi_not(?P<no_dues_id>\d+)/$', views.approve_vlsi_not, name='approve_vlsi_not'),
    url(r'^approve_ece_not(?P<no_dues_id>\d+)/$', views.approve_ece_not, name='approve_ece_not'),
    url(r'^approve_hostel_not(?P<no_dues_id>\d+)/$', views.approve_hostel_not, name='approve_hostel_not'),
    url(r'^approve_library_not(?P<no_dues_id>\d+)/$', views.approve_library_not, name='approve_library_not'),
    url(r'^approve_workshop_not(?P<no_dues_id>\d+)/$', views.approve_workshop_not, name='approve_workshop_not'),
    url(r'^approve_mecha_not(?P<no_dues_id>\d+)/$', views.approve_mecha_not, name='approve_mecha_not'),
    url(r'^approve_mess_not(?P<no_dues_id>\d+)/$', views.approve_mess_not, name='approve_mess_not'),
    url(r'^approve_physics_not(?P<no_dues_id>\d+)/$', views.approve_physics_not, name='approve_physics_not'),
    
            

    url(r'^Bank_nodues_not/$', views.Bank_nodues_not, name='Bank_nodues_not'),
    url(r'^BTP_nodues_not/$', views.BTP_nodues_not, name='BTP_nodues_not'),
    url(r'^CSE_nodues_not/$', views.CSE_nodues_not, name='CSE_nodues_not'),
    url(r'^Design_nodues_not/$', views.Design_nodues_not, name='Design_nodues_not'),
    url(r'^dsa_nodues_not/$', views.dsa_nodues_not, name='dsa_nodues_not'),
    url(r'^Ece_nodues_not/$', views.Ece_nodues_not, name='Ece_nodues_not'),
    url(r'^hostel_nodues_not/$', views.hostel_nodues_not, name='hostel_nodues_not'),
    url(r'^ME_nodues_not/$', views.ME_nodues_not, name='ME_nodues_not'),
    url(r'^library_nodues_not/$', views.library_nodues_not, name='library_nodues_not'),
    url(r'^mess_nodues_not/$', views.mess_nodues_not, name='mess_nodues_not'),
    url(r'^Physics_nodues_not/$', views.Physics_nodues_not, name='Physics_nodues_not'),
    url(r'^discipline_nodues_not/$', views.discipline_nodues_not, name='discipline_nodues_not'),
    


    url(r'^noduesStatus_acad/$', views.noduesStatus_acad, name='noduesStatus_acad'),
  

  url(r'^assistantship/$', views.assistantship, name='assistantship'),
     url(r'^submitform/$', views.assistantship_form_submission, name='assistantship_form_submission'),
    #  url(r'^approveform/$', views.assistantship_form_approval, name='assistantship_approval'),

    url(r'^approveform/$', views.assistantship_form_approval, name='assistantship_form_approval'),
    url(r'^assitantship/thesis_approveform/$', views.assistantship_thesis, name='assistantship_thesis'),
    url(r'^assitantship/hod_approveform/$', views.assistantship_hod, name='assistantship_hod'),
    url(r'^assitantship/acad_approveform/$', views.assistantship_acad_approveform, name='assistantship_acad_approveform'),
    url(r'^assistantship_status/$', views.assistantship_status, name='assistantship_status'),
    url(r'^assistantship_log/$', views.assistantship_log, name='assistantship_log'),
        
    #   url(r'^noduesverification/$', views.nodues, name='nodues'),

    url(r'^assistanship_ta_approve(?P<ass_id>\d+)/$', views.assistanship_ta_approve, name='assistanship_ta_approve'),
    url(r'^assistanship_ta_reject(?P<ass_id>\d+)/$', views.assistanship_ta_reject, name='assistanship_ta_reject'),
     url(r'^assistanship_thesis_approve(?P<ass_id>\d+)/$', views.assistanship_thesis_approve, name='assistanship_thesis_approve'),
    url(r'^assistanship_thesis_reject(?P<ass_id>\d+)/$', views.assistanship_thesis_reject, name='assistanship_thesis_reject'),
     url(r'^assistanship_hod_approve(?P<ass_id>\d+)/$', views.assistanship_hod_approve, name='assistanship_hod_approve'),
    url(r'^assistanship_hod_reject(?P<ass_id>\d+)/$', views.assistanship_hod_reject, name='assistanship_hod_reject'),
     url(r'^assistanship_acad_approve(?P<ass_id>\d+)/$', views.assistanship_acad_approve, name='assistanship_acad_approve'),
    url(r'^assistanship_acad_reject(?P<ass_id>\d+)/$', views.assistanship_acad_reject, name='assistanship_acad_reject'),


    url(r'^othersPage/$', views.othersPage, name='othersPage'),

    url(r'^othersLeave/$', views.othersLeave, name='othersLeave'),
    url(r'^othersGraduate/$', views.othersGraduate, name='othersGraduate'),
    url(r'^othersAssistantship/$', views.othersAssistantship, name='othersAssistanship'),
    url(r'^othersNoDues/$', views.othersNoDues, name='othersNoDues'),



]

