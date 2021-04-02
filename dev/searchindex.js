Search.setIndex({docnames:["api/traits_futures","api/traits_futures.api","api/traits_futures.background_call","api/traits_futures.background_iteration","api/traits_futures.background_progress","api/traits_futures.base_future","api/traits_futures.exception_handling","api/traits_futures.future_states","api/traits_futures.i_future","api/traits_futures.i_message_router","api/traits_futures.i_parallel_context","api/traits_futures.i_pingee","api/traits_futures.i_task_specification","api/traits_futures.multiprocessing_context","api/traits_futures.multiprocessing_router","api/traits_futures.multithreading_context","api/traits_futures.multithreading_router","api/traits_futures.null","api/traits_futures.null.gui_test_assistant","api/traits_futures.null.init","api/traits_futures.null.pinger","api/traits_futures.qt","api/traits_futures.qt.gui_test_assistant","api/traits_futures.qt.init","api/traits_futures.qt.pinger","api/traits_futures.toolkit_support","api/traits_futures.traits_executor","api/traits_futures.version","api/traits_futures.wrappers","api/traits_futures.wx","api/traits_futures.wx.gui_test_assistant","api/traits_futures.wx.init","api/traits_futures.wx.pinger","guide/advanced","guide/cancel","guide/contexts","guide/intro","guide/testing","index"],envversion:{"sphinx.domains.c":2,"sphinx.domains.changeset":1,"sphinx.domains.citation":1,"sphinx.domains.cpp":3,"sphinx.domains.index":1,"sphinx.domains.javascript":2,"sphinx.domains.math":2,"sphinx.domains.python":2,"sphinx.domains.rst":2,"sphinx.domains.std":2,"sphinx.ext.intersphinx":1,"sphinx.ext.viewcode":1,sphinx:56},filenames:["api/traits_futures.rst","api/traits_futures.api.rst","api/traits_futures.background_call.rst","api/traits_futures.background_iteration.rst","api/traits_futures.background_progress.rst","api/traits_futures.base_future.rst","api/traits_futures.exception_handling.rst","api/traits_futures.future_states.rst","api/traits_futures.i_future.rst","api/traits_futures.i_message_router.rst","api/traits_futures.i_parallel_context.rst","api/traits_futures.i_pingee.rst","api/traits_futures.i_task_specification.rst","api/traits_futures.multiprocessing_context.rst","api/traits_futures.multiprocessing_router.rst","api/traits_futures.multithreading_context.rst","api/traits_futures.multithreading_router.rst","api/traits_futures.null.rst","api/traits_futures.null.gui_test_assistant.rst","api/traits_futures.null.init.rst","api/traits_futures.null.pinger.rst","api/traits_futures.qt.rst","api/traits_futures.qt.gui_test_assistant.rst","api/traits_futures.qt.init.rst","api/traits_futures.qt.pinger.rst","api/traits_futures.toolkit_support.rst","api/traits_futures.traits_executor.rst","api/traits_futures.version.rst","api/traits_futures.wrappers.rst","api/traits_futures.wx.rst","api/traits_futures.wx.gui_test_assistant.rst","api/traits_futures.wx.init.rst","api/traits_futures.wx.pinger.rst","guide/advanced.rst","guide/cancel.rst","guide/contexts.rst","guide/intro.rst","guide/testing.rst","index.rst"],objects:{"":{traits_futures:[0,0,0,"-"]},"traits_futures.background_call":{BackgroundCall:[2,1,1,""],CallBackgroundTask:[2,1,1,""],CallFuture:[2,1,1,""],submit_call:[2,4,1,""]},"traits_futures.background_call.BackgroundCall":{args:[2,2,1,""],background_task:[2,3,1,""],callable:[2,2,1,""],future:[2,3,1,""],kwargs:[2,2,1,""]},"traits_futures.background_iteration":{BackgroundIteration:[3,1,1,""],GENERATED:[3,5,1,""],IterationBackgroundTask:[3,1,1,""],IterationFuture:[3,1,1,""],submit_iteration:[3,4,1,""]},"traits_futures.background_iteration.BackgroundIteration":{args:[3,2,1,""],background_task:[3,3,1,""],callable:[3,2,1,""],future:[3,3,1,""],kwargs:[3,2,1,""]},"traits_futures.background_iteration.IterationFuture":{result_event:[3,2,1,""]},"traits_futures.background_progress":{BackgroundProgress:[4,1,1,""],PROGRESS:[4,5,1,""],ProgressBackgroundTask:[4,1,1,""],ProgressFuture:[4,1,1,""],ProgressReporter:[4,1,1,""],submit_progress:[4,4,1,""]},"traits_futures.background_progress.BackgroundProgress":{args:[4,2,1,""],background_task:[4,3,1,""],callable:[4,2,1,""],future:[4,3,1,""],kwargs:[4,2,1,""]},"traits_futures.background_progress.ProgressFuture":{progress:[4,2,1,""]},"traits_futures.background_progress.ProgressReporter":{report:[4,3,1,""]},"traits_futures.base_future":{BaseFuture:[5,1,1,""]},"traits_futures.base_future.BaseFuture":{cancel:[5,3,1,""],cancellable:[5,2,1,""],done:[5,2,1,""],exception:[5,3,1,""],result:[5,3,1,""],state:[5,2,1,""]},"traits_futures.exception_handling":{marshal_exception:[6,4,1,""]},"traits_futures.future_states":{CANCELLABLE_STATES:[7,5,1,""],CANCELLED:[7,5,1,""],CANCELLING:[7,5,1,""],COMPLETED:[7,5,1,""],DONE_STATES:[7,5,1,""],EXECUTING:[7,5,1,""],FAILED:[7,5,1,""],FutureState:[7,2,1,""],WAITING:[7,5,1,""]},"traits_futures.i_future":{IFuture:[8,1,1,""]},"traits_futures.i_future.IFuture":{cancel:[8,3,1,""],cancellable:[8,2,1,""],done:[8,2,1,""],exception:[8,3,1,""],message:[8,2,1,""],result:[8,3,1,""],state:[8,2,1,""]},"traits_futures.i_message_router":{IMessageReceiver:[9,1,1,""],IMessageRouter:[9,1,1,""],IMessageSender:[9,1,1,""]},"traits_futures.i_message_router.IMessageReceiver":{message:[9,2,1,""]},"traits_futures.i_message_router.IMessageRouter":{close_pipe:[9,3,1,""],pipe:[9,3,1,""],start:[9,3,1,""],stop:[9,3,1,""]},"traits_futures.i_message_router.IMessageSender":{send:[9,3,1,""],start:[9,3,1,""],stop:[9,3,1,""]},"traits_futures.i_parallel_context":{IParallelContext:[10,1,1,""]},"traits_futures.i_parallel_context.IParallelContext":{close:[10,3,1,""],closed:[10,3,1,""],event:[10,3,1,""],message_router:[10,3,1,""],worker_pool:[10,3,1,""]},"traits_futures.i_pingee":{IPingee:[11,1,1,""],IPinger:[11,1,1,""]},"traits_futures.i_pingee.IPingee":{connect:[11,3,1,""],disconnect:[11,3,1,""]},"traits_futures.i_pingee.IPinger":{connect:[11,3,1,""],disconnect:[11,3,1,""],ping:[11,3,1,""]},"traits_futures.i_task_specification":{ITaskSpecification:[12,1,1,""]},"traits_futures.i_task_specification.ITaskSpecification":{background_task:[12,3,1,""],future:[12,3,1,""]},"traits_futures.multiprocessing_context":{MultiprocessingContext:[13,1,1,""]},"traits_futures.multiprocessing_context.MultiprocessingContext":{close:[13,3,1,""],closed:[13,3,1,""],event:[13,3,1,""],message_router:[13,3,1,""],worker_pool:[13,3,1,""]},"traits_futures.multiprocessing_router":{MultiprocessingReceiver:[14,1,1,""],MultiprocessingRouter:[14,1,1,""],MultiprocessingSender:[14,1,1,""],monitor_queue:[14,4,1,""]},"traits_futures.multiprocessing_router.MultiprocessingReceiver":{connection_id:[14,2,1,""],message:[14,2,1,""]},"traits_futures.multiprocessing_router.MultiprocessingRouter":{close_pipe:[14,3,1,""],manager:[14,2,1,""],pipe:[14,3,1,""],start:[14,3,1,""],stop:[14,3,1,""]},"traits_futures.multiprocessing_router.MultiprocessingSender":{send:[14,3,1,""],start:[14,3,1,""],stop:[14,3,1,""]},"traits_futures.multithreading_context":{MultithreadingContext:[15,1,1,""]},"traits_futures.multithreading_context.MultithreadingContext":{close:[15,3,1,""],closed:[15,3,1,""],event:[15,3,1,""],message_router:[15,3,1,""],worker_pool:[15,3,1,""]},"traits_futures.multithreading_router":{MultithreadingReceiver:[16,1,1,""],MultithreadingRouter:[16,1,1,""],MultithreadingSender:[16,1,1,""]},"traits_futures.multithreading_router.MultithreadingReceiver":{connection_id:[16,2,1,""],message:[16,2,1,""]},"traits_futures.multithreading_router.MultithreadingRouter":{close_pipe:[16,3,1,""],pipe:[16,3,1,""],start:[16,3,1,""],stop:[16,3,1,""]},"traits_futures.multithreading_router.MultithreadingSender":{send:[16,3,1,""],start:[16,3,1,""],stop:[16,3,1,""]},"traits_futures.null":{gui_test_assistant:[18,0,0,"-"],init:[19,0,0,"-"],pinger:[20,0,0,"-"]},"traits_futures.null.gui_test_assistant":{GuiTestAssistant:[18,1,1,""],TIMEOUT:[18,5,1,""]},"traits_futures.null.gui_test_assistant.GuiTestAssistant":{run_until:[18,3,1,""],setUp:[18,3,1,""],tearDown:[18,3,1,""]},"traits_futures.null.init":{toolkit_object:[19,5,1,""]},"traits_futures.null.pinger":{Pingee:[20,1,1,""],Pinger:[20,1,1,""]},"traits_futures.null.pinger.Pingee":{connect:[20,3,1,""],disconnect:[20,3,1,""]},"traits_futures.null.pinger.Pinger":{connect:[20,3,1,""],disconnect:[20,3,1,""],ping:[20,3,1,""]},"traits_futures.qt":{gui_test_assistant:[22,0,0,"-"],init:[23,0,0,"-"],pinger:[24,0,0,"-"]},"traits_futures.qt.gui_test_assistant":{GuiTestAssistant:[22,1,1,""],TIMEOUT:[22,5,1,""]},"traits_futures.qt.gui_test_assistant.GuiTestAssistant":{run_until:[22,3,1,""],setUp:[22,3,1,""],tearDown:[22,3,1,""]},"traits_futures.qt.init":{toolkit_object:[23,5,1,""]},"traits_futures.qt.pinger":{Pingee:[24,1,1,""],Pinger:[24,1,1,""]},"traits_futures.qt.pinger.Pingee":{connect:[24,3,1,""],disconnect:[24,3,1,""]},"traits_futures.qt.pinger.Pinger":{connect:[24,3,1,""],disconnect:[24,3,1,""],ping:[24,3,1,""]},"traits_futures.toolkit_support":{Toolkit:[25,1,1,""],toolkit:[25,5,1,""]},"traits_futures.toolkit_support.Toolkit":{toolkit_object:[25,3,1,""]},"traits_futures.traits_executor":{ExecutorState:[26,2,1,""],RUNNING:[26,5,1,""],STOPPED:[26,5,1,""],STOPPING:[26,5,1,""],TraitsExecutor:[26,1,1,""]},"traits_futures.traits_executor.TraitsExecutor":{running:[26,2,1,""],state:[26,2,1,""],stop:[26,3,1,""],stopped:[26,2,1,""],submit:[26,3,1,""],submit_call:[26,3,1,""],submit_iteration:[26,3,1,""],submit_progress:[26,3,1,""]},"traits_futures.version":{version:[27,5,1,""]},"traits_futures.wrappers":{BackgroundTaskWrapper:[28,1,1,""],CONTROL:[28,5,1,""],CUSTOM:[28,5,1,""],FutureWrapper:[28,1,1,""],RAISED:[28,5,1,""],RETURNED:[28,5,1,""],STARTED:[28,5,1,""]},"traits_futures.wrappers.BackgroundTaskWrapper":{send_control_message:[28,3,1,""],send_custom_message:[28,3,1,""]},"traits_futures.wrappers.FutureWrapper":{done:[28,2,1,""],future:[28,2,1,""],receiver:[28,2,1,""]},"traits_futures.wx":{gui_test_assistant:[30,0,0,"-"],init:[31,0,0,"-"],pinger:[32,0,0,"-"]},"traits_futures.wx.gui_test_assistant":{AppForTesting:[30,1,1,""],GuiTestAssistant:[30,1,1,""],TIMEOUT:[30,5,1,""],TimeoutTimer:[30,1,1,""]},"traits_futures.wx.gui_test_assistant.AppForTesting":{OnInit:[30,3,1,""],close:[30,3,1,""],exit:[30,3,1,""]},"traits_futures.wx.gui_test_assistant.GuiTestAssistant":{run_until:[30,3,1,""],setUp:[30,3,1,""],tearDown:[30,3,1,""]},"traits_futures.wx.gui_test_assistant.TimeoutTimer":{Notify:[30,3,1,""],start:[30,3,1,""],stop:[30,3,1,""]},"traits_futures.wx.init":{toolkit_object:[31,5,1,""]},"traits_futures.wx.pinger":{Pingee:[32,1,1,""],Pinger:[32,1,1,""]},"traits_futures.wx.pinger.Pingee":{connect:[32,3,1,""],disconnect:[32,3,1,""]},"traits_futures.wx.pinger.Pinger":{connect:[32,3,1,""],disconnect:[32,3,1,""],ping:[32,3,1,""]},traits_futures:{"null":[17,0,0,"-"],api:[1,0,0,"-"],background_call:[2,0,0,"-"],background_iteration:[3,0,0,"-"],background_progress:[4,0,0,"-"],base_future:[5,0,0,"-"],exception_handling:[6,0,0,"-"],future_states:[7,0,0,"-"],i_future:[8,0,0,"-"],i_message_router:[9,0,0,"-"],i_parallel_context:[10,0,0,"-"],i_pingee:[11,0,0,"-"],i_task_specification:[12,0,0,"-"],multiprocessing_context:[13,0,0,"-"],multiprocessing_router:[14,0,0,"-"],multithreading_context:[15,0,0,"-"],multithreading_router:[16,0,0,"-"],qt:[21,0,0,"-"],toolkit_support:[25,0,0,"-"],traits_executor:[26,0,0,"-"],version:[27,0,0,"-"],wrappers:[28,0,0,"-"],wx:[29,0,0,"-"]}},objnames:{"0":["py","module","Python module"],"1":["py","class","Python class"],"2":["py","attribute","Python attribute"],"3":["py","method","Python method"],"4":["py","function","Python function"],"5":["py","data","Python data"]},objtypes:{"0":"py:module","1":"py:class","2":"py:attribute","3":"py:method","4":"py:function","5":"py:data"},terms:{"100":[34,35],"10101":36,"1024":35,"128":35,"192":35,"2018":[33,34,35,37,38],"2021":[33,34,35,37,38],"243":37,"255":35,"50th":34,"768":35,"\u03c0":38,"abstract":[8,9,10,11,12],"boolean":[18,22,30,33,38],"case":[14,16,26,33,35,36],"class":[1,2,3,4,5,7,8,9,10,11,12,13,14,15,16,18,19,20,22,23,24,25,26,28,30,31,32,33,34,35,36,37,38],"default":[8,9,18,22,26,30,33,35,36],"enum":[7,26],"export":1,"final":[7,34,35,36],"float":[18,22,30],"function":[0,2,3,4,5,8,20,24,26,32,33,34,35,36,38],"import":[1,33,34,35,36,37,38],"int":[10,13,14,15,16,26,33,34,36,38],"long":[14,35,37,38],"new":[9,13,14,15,16,26,34,35,36,37,38],"null":[0,38],"public":1,"return":[2,3,4,5,8,9,10,12,13,14,15,16,18,22,26,28,30,33,34,35,36,38],"throw":34,"true":[5,8,10,12,13,15,18,22,26,30,33,34,35,36,38],"try":35,"while":[9,12,14,16,33,38],Adding:34,But:34,For:[14,33,34,35,36,37],Its:36,Not:[9,11,14,16],One:[5,8],That:[34,36],The:[2,3,4,5,8,9,10,11,12,14,16,18,19,20,22,23,24,25,26,28,30,31,32,34,35,36,37,38],These:[4,26,28],Use:[26,34],Using:38,With:33,__main__:[33,34,35],__name__:[33,34,35],_cancel_all_fir:35,_cancel_running_task:33,_clear_finished_fir:35,_get_bg_color:35,_get_can_calcul:[33,34],_get_can_cancel:[33,34],_get_no_running_futur:38,_get_state_text:35,_local_message_queu:14,_monitor_thread:14,_process_:33,_process_buzz:33,_process_fizz:33,_process_fizz_buzz:33,_process_message_queu:14,_record_result:36,_report_buzz:33,_report_fizz:33,_report_fizz_buzz:33,_report_partial_result:34,_report_progress:36,_report_result:[34,38],_request_cancel:34,_reset_futur:33,_route_messag:14,_square_fir:35,_submit_background_cal:38,_submit_calcul:[33,34],_task_sent:33,_update_result:36,abc:[2,3,4,10,11,12,28,33],abil:[18,22,30,34],abort:36,about:[5,8,34,36,38],abov:[33,34,36,37],abstractcontextmanag:9,accept:[2,3,4,26,33,36],access:[5,8,25,36,38],accompani:33,accur:38,achiev:35,acknowledg:36,across:6,actual:[2,9,37],adapt:[8,9,35],adaptation_error:[8,9],adaptationerror:[8,9],adapte:[8,9],add:34,addit:[4,28,34,35,36],advanc:38,advis:36,aforement:[33,34,35,37,38],after:[9,11,14,16,20,24,32,33,34,36,37],again:37,alert:14,algorithm:34,alia:26,all:[9,14,16,28,34,35,36,37,38],alloc:9,allow:[11,14,16,18,22,30,33,34,35,36],alreadi:[5,8,9,11,14,16,20,24,30,32,34,36],also:[4,9,14,33,34,35,36,37,38],alwai:[5,8,9,11,14,16,28],ani:[5,8,9,10,11,12,13,14,15,16,20,24,28,30,32,33,34,36],anoth:36,anyth:33,apart:34,api:[0,10,33,34,35,36,37],app:30,append:[35,36],appfortest:30,appli:28,applic:[30,34,36,38],appropri:[9,26],approxim:38,approximate_pi:34,arbitrari:[4,18,22,26,30,36],arg:[2,3,4,24,26,30,32],argument:[2,3,4,11,12,18,20,22,24,26,28,30,32,33,36],around:[2,25,34],arriv:[3,4,9,14,33,36,38],assertequ:37,asserteventuallytrueingui:37,assign:34,associ:36,assum:[14,26,36],asynchron:36,asyncio:20,attempt:[5,8,36],attribut:[5,8,33,34,36],attributeerror:[5,8,36],austin:[33,34,35,37,38],auto_upd:35,avail:[5,8,33,34,35,36,37,38],avoid:37,await:7,back:[12,14,16],backend:25,background:[0,2,3,4,5,6,7,8,9,11,12,14,16,20,24,26,28,32,34,35,37],background_cal:[0,38],background_iter:[0,38],background_progress:[0,38],background_task:[2,3,4,12,28,33],backgroundcal:[2,12],backgroundfizzbuzz:33,backgrounditer:[3,12],backgroundprogress:4,backgroundtaskwrapp:28,base:[2,3,4,5,8,9,10,11,12,13,14,15,16,18,20,22,24,25,26,28,30,32,33,36,38],base_futur:[0,2,3,4,38],base_toolkit:[19,23,31],basefutur:[1,2,3,4,5,8,33],basic:[33,34],becaus:[36,37],been:[2,3,4,5,7,8,9,12,14,16,26,28,33,36],befor:[9,10,11,13,14,15,16,18,20,22,24,28,30,32,34,36],behaviour:34,being:[28,37],below:33,best:[5,8,36],between:[9,14],bit:36,block:37,bool:[5,8,26,28,33,34,38],both:[12,26,34],bound:35,boundari:6,brief:[34,36],bsd:[33,34,35,37,38],busi:36,button:[33,34,35,38],buzz:38,calcul:[33,34,35,36,38],call:[2,3,4,9,11,12,14,16,18,20,22,24,26,28,30,32,33,34,36,37,38],callabl:[2,3,4,11,12,18,20,22,24,26,28,30,32,34,36,38],callback:[14,20,24,30,32],callbackgroundtask:2,callfutur:[1,2,26,34,35,36,38],can:[2,3,4,5,6,8,9,10,12,13,14,15,16,20,24,26,28,30,32,33,34,35,36,37,38],can_calcul:[33,34],can_cancel:[33,34],cancel:[1,2,3,4,5,7,8,12,26,28,33,35,37,38],cancel_al:35,cancel_ev:28,cancellable_st:7,cannot:36,carlo:34,carri:34,caus:36,challeng:37,chang:[5,8,18,22,28,30,34,36,38],channel:9,check:[2,3,4,12,28,33,34,37],child:14,choic:[13,15,26],choos:[10,33,36],chunk:36,circl:34,clean:30,cleaner:33,cleanup:[10,13,15],clear:35,clear_finish:35,close:[9,10,13,14,15,16,30,35],close_pip:[9,14,16],code:[4,30,33,34,35,38],collect:[2,3,4,28,33],color:35,column:35,com:[33,34,35,37,38],come:33,common:5,commun:[4,5,8,9,14,16,28,33,37],compar:34,compat:[26,35],complet:[1,5,7,8,26,28,30,34,35,36,37,38],compon:36,compound:36,comput:[34,35,36,37,38],concurr:[2,10,13,15,26,35,36,38],condit:[18,22,30,33,34,35,37,38],configure_trait:[33,34,35,38],connect:[9,11,14,16,20,24,32],connection_id:[14,16],consist:[2,5,8,36],constant:[1,5,8,12,33],construct:35,consum:12,contain:[1,5,8,12,28,34,36],content:4,context:[0,10,13,15,26,38],contextlib:9,continu:14,control:28,conveni:[2,3,4,5,26,33,36],convers:34,cooper:[34,38],copi:38,copyright:[33,34,35,37,38],core:[1,10],correspond:[4,12,26,33,34,36],could:34,count:[33,34],coupl:33,cours:36,cpu:35,creat:[9,11,12,14,16,26,35,36,38],creator:26,cross:[11,20,24,32,38],crude:34,current:[9,14,16,25,26,33,35,36,37,38],current_futur:35,current_step:36,custom:[8,28,33],data:36,deadlock:38,deal:[12,36],decid:38,dedic:33,def:[33,34,35,36,37,38],default_traits_view:35,defin:[0,33,38],deleg:[13,15,26,28],deliv:37,demonstr:[33,34,35],depend:[10,35,36],depends_on:[33,34,38],deprec:26,deriv:[26,36],describ:[12,33,34,35,36,37,38],design:[37,38],desir:35,desktop:34,detail:[6,9,33,34,36],determin:14,dev0:[27,38],diagram:36,dict:[2,3,4,30,35,36],dictionari:30,differ:[33,35,36],directli:[33,36],discard:9,disconnect:[11,20,24,32],dispatch:[9,33,38],displai:35,dispos:[9,10,13,15,26],doe:[4,33,34,37],doesn:[34,36],don:[33,34,37],done:[5,8,28,33,34,35,36,37,38],done_st:7,down:[26,36,37],dure:[33,34,36],each:[8,14,33,34,35,36,37],easi:[34,37],easili:38,editor:35,effect:[9,37],either:[5,12,36],elif:[33,34,35],elimin:38,els:[5,8,10,13,15,34,35],emit:11,emitt:[20,24,32],enabl:[33,34,38],enabled_when:[33,34,38],encapsul:33,encount:34,end:[2,4,9,14,16,33,34,36,37],ensur:[9,11,30],enthought:[33,34,35,37,38],entri:[19,23,31,36],error:[7,34,36],evalu:[18,22,30],even:36,event:[3,4,8,9,10,11,13,14,15,16,18,22,30,33,34,35,36,37,38],eventu:[4,11,34,36,37],ever:34,everi:[4,11,18,20,22,24,30,32,34],everyth:[1,33],exactli:[5,8,36],examin:36,exampl:[10,26,35,36,38],exc_info:[5,8],except:[5,6,7,8,12,18,22,28,30,33,34,35,36],exception_handl:[0,38],exclus:26,execut:[1,2,3,4,5,7,8,12,14,16,20,24,26,30,32,33,34,35,36,37],executor:[0,2,3,4,8,10,13,15,26,28,33,34,35,37,38],executorst:[1,26,36],exist:[26,36],exit:[30,36],exit_cod:30,expect:[20,24,32,33,34,35,36,37],expert:38,expir:30,explicitli:36,expovari:35,express:34,extend:38,face:37,facil:38,fact:36,factori:33,fail:[1,5,7,8,34,35,36,37],failur:36,fals:[5,8,10,12,13,15,26,28,33],far:36,find:[19,23,31,37],finish:[9,14,16,36],fire:[3,4,5,8,9,14,16,33,38],first:[25,33],fix:[20,24,25,32],fizz:38,fizz_buzz:33,fizz_buzz_task:33,fizzbuzzfutur:33,fizzbuzzui:33,flavour:[5,9],follow:[1,14,34,36],foreground:[3,9,12,14,16,28,38],forev:37,form:[5,8,10,12,34,36],format:[5,8,33,35,36,38],fortun:34,friendli:[13,15],from:[1,3,4,5,6,7,8,9,10,11,14,16,18,20,22,24,28,30,32,33,34,35,36,37,38],front:[2,4,33],fulli:37,further:[5,8,34,36],futur:[0,2,3,4,5,7,8,9,10,12,13,15,26,28,34,35],future_st:[0,38],futurest:[1,5,7,8,36],futurewrapp:28,game:33,gener:[3,33,34],get:[33,34,38],give:[4,33,36,37],given:[3,9,10,13,15,18,20,22,24,26,28,30,32,33,36,38],goe:34,guarante:1,gui:[9,14,16,34,35,37,38],gui_test_assist:[0,17,21,29,37,38],guid:[34,36],guitestassist:[18,22,30,37],half:[9,14,16],hand:35,handl:[2,4,28,33],handler:[33,35],hang:37,happen:36,has:[2,3,4,5,7,8,9,12,14,16,26,28,33,34,35,36,37],has_trait:[2,3,4,5,8,9,14,16,18,22,26,28,30],hasn:30,hasrequiredtrait:14,hasstricttrait:[2,3,4,5,14,16,26,28,33,34,38],hastrait:[18,22,28,30,38],have:[10,12,30,33,36,37],heavili:35,height:35,here:[12,33,34,35,36,37,38],hgroup:[33,34,35],high:[34,35],higher:35,hint:37,hit:37,hold:[18,22,30],hook:36,how:[12,33,34,35,36],howev:[34,36],http:[33,34,35,37,38],i_futur:[0,38],i_message_rout:[0,38],i_parallel_context:[0,13,15,38],i_pinge:[0,38],i_task_specif:[0,38],ideal:[4,33,34],identifi:33,ifutur:[1,8,12,26,28,33,34],illustr:34,imessagereceiv:[9,14,16],imessagerout:[9,10,14,16],imessagesend:[9,14,16,28],immedi:[5,8,14,36,38],immut:[4,9,12,14,16,33,34],implement:[0,9,10,12,16,33,34,35,38],impli:36,inc:[33,34,35,37,38],includ:[4,26,33,34,35,36,37,38],incom:[14,38],increas:34,index:38,indic:[12,28],ineffici:34,inform:[4,5,6,8,27,28,34,36,38],ingredi:33,inherit:33,init:[0,17,21,29,38],initi:[26,36],input:[18,22,30,35,38],input_for_calcul:38,insert:34,insid:34,inspect:14,instal:37,instanc:[9,11,14,16,28,33,34,35,36,38],instanti:[14,16,36],instead:[5,8,26,34,35,36,37],integ:[33,35,36],integr:38,intend:33,interact:[37,38],interest:[36,37],interfac:[8,9,10,11,12,14,16,33,35],intern:35,interpret:[4,8,36],interrog:33,interrupt:[36,38],interruptible_sum_of_squar:36,interruptible_task:34,interruptibletaskexampl:34,interv:36,introduc:36,introduct:38,invok:12,iparallelcontext:[1,10,13,15,26,35],iping:11,ipinge:[11,14,16],is_set:10,isn:33,issu:38,itaskspecif:[1,12,26,33],item:[34,35,36,38],iter:[3,26,33,34,36,38],iterationbackgroundtask:3,iterationfutur:[1,3,26,34,36],its:[5,9,14,33,34,35,36,37,38],itself:37,job:[9,12,26,33,35,36,37],jobtabularadapt:35,just:34,keep:[37,38],kei:36,kept:[9,14,16],keyword:30,know:[12,35],knowledg:[5,8,36],known:33,kwarg:[2,3,4,24,26,30,32],lambda:37,land:34,laptop:34,larg:[36,38],larger:35,last:[33,38],latenc:34,later:[33,38],layer:9,leak:37,least:[30,33],leav:38,length:36,level:36,librari:1,licens:[33,34,35,37,38],like:[8,10,13,15,26,33,34,35,36],likelihood:35,line:34,link:[4,9,11,20,24,32],list:35,listen:[5,8,9,14,34,36],littl:36,local:14,local_queu:14,log:[9,14,16,34],logic:10,longer:[20,24,26,30,32,35,36],look:[33,36],loop:[9,11,14,18,22,30,37,38],low:35,machin:[10,34],machineri:[5,14,28,36],made:[1,9,11,14,16,20,24,32,33],mai:[4,11,12,33,34,35,36,37,38],main:[9,11,12,14,16,20,24,30,32,35,36,37,38],make:[33,35,37,38],manag:[14,26],manner:[20,24,32],mark:4,marshal_except:6,match:[14,16,36],max_step:36,max_work:[10,13,15,26,36],maximum:[10,13,15,26,37],mean:[9,34,36,37,38],mean_tim:35,mechan:[11,33],meet:33,mention:[34,36],messag:[2,3,4,7,8,9,10,12,13,14,15,16,28,34,36,38],message_arg:[8,12,28],message_argu:33,message_queu:[14,16],message_rout:[10,13,15],message_typ:[8,12,28,33],method:[9,10,11,14,16,20,24,26,32,33,34,35,36,37],mid:34,might:36,minim:38,minimum:10,modif:34,modifi:34,modul:[0,17,21,29,36,38],monitor:[2,3,4,12,14,18,22,30,33,36],monitor_queu:14,mont:34,more:[7,9,14,16,34,35,36],most:33,move:[5,8,14,34,36],multipl:[33,35,36],multiprocess:[10,13,14,26,38],multiprocessing_context:[0,38],multiprocessing_rout:[0,38],multiprocessingcontext:[1,13,35],multiprocessingreceiv:14,multiprocessingrout:[13,14],multiprocessingsend:14,multithread:[10,15,26,36],multithreading_context:[0,38],multithreading_rout:[0,38],multithreadingcontext:[1,15,35],multithreadingreceiv:16,multithreadingrout:[15,16],multithreadingsend:16,must:[4,9,14,16,20,24,26,32,33,34,36,37],mutat:33,mutual:26,my_executor:36,my_result:36,n_is_multiple_of_3:33,n_is_multiple_of_5:33,name:[2,3,4,18,22,26,30,33,36,38],necessari:[9,10,13,14,15,16,33],necessarili:36,need:[1,9,10,26,30,33,34,35,36,37,38],never:[36,37],next:[9,14,33,36],no_running_futur:38,non_interruptible_task:34,none:[10,13,14,15,26,28,33,34,38],noninterruptibletaskexampl:34,note:[12,26,33,34,37],noth:33,notifi:[14,16,30],now:[33,34],number:[10,13,15,18,22,26,30,33,34],object:[2,3,4,5,8,9,12,14,16,18,19,20,22,23,24,25,26,28,30,31,32,33,34,35,38],oblig:12,observ:[33,34],obtain:[5,8],occur:[5,8,14,34,36,37],off:[35,38],often:34,old:26,on_p:[11,14,20,24,32],on_trait_chang:[36,38],onc:[5,8,26,34,35,36],one:[5,7,8,30,34,36,37],ones:26,ongo:34,oninit:30,onli:[5,8,9,11,18,22,30,33,34,35,36,37,38],onlin:[33,34,35,37,38],onto:14,open:[33,34,35,37,38],oper:[33,35],option:[10,12,13,15,18,22,26,28,30,33],order:[9,34,36,37,38],origin:34,other:[1,4,10,12,33,38],otherwis:33,our:[33,37],out:[18,22,30,34],overrid:30,overridden:33,overview:[0,38],own:[11,14,35,36,38],ownership:9,packag:[1,27,36,38],page:38,pair:[9,14,16,36],parallel:[0,10,26,38],paramet:[2,3,4,9,10,11,13,14,15,16,18,20,22,24,26,28,30,32,33,36],parameterless:[20,24,32],part:33,partial:38,particular:[10,11,12,37],pass:[2,3,4,9,14,16,26,28,30,33,35,36],pattern:38,payload:[33,34],pend:[14,16],per:34,perform:37,perhap:10,permit:[7,9,14,16],pickleabl:[4,9,12,14,16,33,34],piec:[5,33],ping:[11,14,16,20,24,32],pinge:[11,14,16,20,24,32],pinger:[0,11,17,21,29,38],pipe:[9,14,16],place:[14,33],plain:34,platform:38,player:36,plu:[33,34],point:[4,5,8,18,19,22,23,30,31,34,36,37],pool:[4,10,13,15,26,35,38],portion:4,posit:[2,3,4,26,30,33,36],possibl:[33,34,36],potenti:[37,38],pow:37,prefer:33,prefix:28,prepar:[9,11,14,16,20,24,32],present:[10,38],press:[34,38],prevent:[26,37],previou:[34,38],previous:[9,14,16,36],primit:[10,26,35],privat:[26,33],process:[6,9,14,28,33,35,36],process_queu:14,processpoolexecutor:13,produc:[9,14,16,36],progress:[4,26,33,34,36,38],progress_info:[4,36],progressbackgroundtask:4,progressfutur:[1,4,26,36],progressreport:4,properti:[5,8,10,13,15,25,26,33,34,35,36,38],proport:34,provid:[2,4,5,8,9,10,11,13,15,18,20,22,24,25,26,28,30,32,33,34,35,36,37,38],proxi:14,pull:14,purpos:[11,35,36],put:[14,36,38],pyfac:[19,23,24,31,37],pyqt:37,pysid:37,python:[12,26,33,34,36,38],qt4:37,qtcore:24,quarter:34,queu:7,queue:[9,14,16,35],quickstartexampl:38,race:38,rais:[5,7,8,9,12,14,16,18,22,28,30,33,34,35,36],random:[34,35],rang:[34,35,36],rare:34,rather:[34,37],reach:[5,8,9,14,16,18,22,30,36,37],react:[9,14,16],readi:33,readonli:[33,34,38],real:25,reason:34,receiv:[7,9,11,14,16,20,24,28,32,33,36,37],recipi:[14,16],record:[12,28,36,38],redistribut:[33,34,35,37,38],refer:34,regardless:[18,22,30],regist:33,relat:[26,35,36],releas:38,reli:37,remain:[9,14,16,34],remov:[9,14,16,35,37],replac:34,report:[4,26,33,36,38],repres:[1,2,3,4,7,26,28,33,34,36],represent:3,request:[2,3,4,5,7,8,9,12,20,24,26,28,32,33,34,36,37],requir:[35,38],reserv:[33,34,35,37,38],resiz:[33,34,35,38],resourc:[9,19,23,26,31],respect:33,respond:38,respons:[7,9,26,34,36,38],rest:37,restart:36,result:[3,5,8,12,28,33,35,37,38],result_ev:[3,34,36],retriev:36,right:[33,34,35,37,38],rout:[9,14,16],router:[9,10,13,14,15,16],row:35,run:[1,2,9,11,14,16,18,22,26,30,33,34,35,36,37,38],run_until:[18,22,30],runtimeerror:[5,8,9,14,16,18,22,30,34,35,36],safe:[5,6,8,9,10,11,13,14,15,16,20,24,26,32,33,34,35,37],safety_timeout:37,same:[9,10,14,16,36],sample_count:34,schedul:[36,37],search:38,second:[18,22,30,33,34,37],section:[33,34,36,37],see:[33,36],self:[14,33,34,35,36,37,38],send:[2,3,4,9,11,12,14,16,20,24,28,32,33,36,38],send_control_messag:28,send_custom_messag:28,sender:[9,14,16,28],sent:[3,4,9,11,14,16,20,24,28,32,33,36],separ:35,sequenc:36,server:14,set:[10,14],setup:[9,14,16,18,22,30,37],sever:[30,34],share:[10,11,13,14,15,38],shareabl:[10,13,15],shot:30,should:[1,3,4,9,10,11,12,14,16,20,24,26,32,33,34,35,36,37],shouldn:34,show:[33,35,36,38],shut:[26,36,37],shutdown:36,side:37,signatur:12,similarli:33,simpl:[2,12,33,34,36,37,38],simplist:34,simultan:35,sinc:[26,33],singl:[4,9,12,18,22,30,36],six:[5,8,36],sleep:[33,35,38],sleep_tim:35,slow:35,slow_squar:[35,38],slowli:[33,34,35,38],small:[9,14,16],smaller:36,softwar:[33,34,35,37,38],sole:11,solut:38,some:[9,33,34,35,36,37],someth:[3,6,34],somewhat:[18,22,30],sourc:[2,3,4,5,6,8,9,10,11,12,13,14,15,16,18,20,22,24,25,26,28,30,32,33,34,35,37,38],space:34,specif:[2,3,4,11,12,19,23,25,31,35,38],specifi:12,squar:[34,35,36,38],squaringhelp:35,stabil:1,standard:33,start:[9,14,16,28,30,34,35,36],state:[0,2,3,4,5,7,8,26,28,33,34,35,37,38],state_text:35,statement:34,statu:[2,3,4,12,33,35],step:[14,36],steps_complet:36,still:[5,8,34,36],stop:[1,9,14,16,26,30,35,37,38],store:36,str:[2,3,4,5,8,18,22,28,30,33,34,35,38],strictli:33,string:[5,8,12,27,33],stringifi:36,structur:9,style:[33,34,38],subclass:[8,30,33],submiss:[0,4,33,34,36,38],submit:[2,3,4,12,26,28,34,35,37,38],submit_cal:[1,2,26,33,34,35,36,37,38],submit_fizz_buzz:33,submit_iter:[1,3,26,33,34,36],submit_progress:[1,4,26,33,36],subpackag:1,succeed:28,success:37,successfulli:36,suit:37,suitabl:[10,13,15,33,38],sum:36,suppli:[26,34],support:[0,4,6,18,22,25,30,38],suppress:33,tabl:[9,14,16,35],tabularadapt:35,tabulareditor:35,take:[8,9,30,34,36],target:[4,10,11,20,24,28,32],task:[0,2,3,4,5,6,7,8,9,12,14,16,26,28,35,37,38],teardown:[9,14,16,18,22,30,37],tell:36,term:[33,34,35,37,38],test:[18,22,30,34,38],test_my_futur:37,testcas:37,testmyfutur:37,text:35,than:[4,34,36,37],thank:[33,34,35,37,38],thei:[8,26,36],them:36,thi:[1,2,3,4,5,8,9,10,11,12,13,14,15,16,18,20,22,24,25,26,28,30,32,33,34,35,36,37,38],thing:33,those:[11,14,33,34,37],though:[33,34],thousand:34,thread:[6,9,10,11,12,14,16,20,24,32,35,36,37,38],thread_pool:26,threadpoolexecutor:[15,36],three:[33,36],through:35,time:[11,18,20,22,24,25,30,32,33,34,35,36,38],timeout:[18,22,30,35,37],timeouttim:30,timer:30,tip:37,titl:35,togeth:38,too:[34,35],took:35,toolkit:[11,19,23,25,31,37],toolkit_object:[19,23,25,31,37],toolkit_support:[0,38],top:36,topic:[36,38],total:[34,36],total_step:36,traceback:[5,8,36],tradit:38,trait:[1,2,3,4,5,7,8,9,14,16,18,22,26,28,30,33,34,35,36],traits_executor:[0,35,38],traits_futur:[33,34,35,36,37,38],traits_view:[33,34,38],traitsexecutor:[1,2,3,4,10,12,13,15,26,28,33,34,35,36,37,38],traitsui:[33,34,35],transfer:[6,14],transit:36,transmit:6,tupl:[2,3,4,5,8,28,30,36],turn:[6,34],two:[33,34,35,36,37],txt:[33,34,35,37,38],type:[0,2,3,4,5,7,8,10,12,13,15,26,28,34,36,38],typic:[9,12,14,16,34,37],uitem:[33,34,35,38],unclos:[9,14,16],under:[11,33,34,35,37,38],underli:[26,28,36],understand:36,undo:[9,11,20,24,32],unexpect:34,unilater:34,unit:[30,34,37],unittest:37,unlik:38,unreli:35,until:[18,20,22,24,30,32,34,37],updat:[36,38],update_plot_data:36,usabl:34,use:[2,3,4,10,13,14,15,20,24,26,32,33,34,35,36,37],used:[2,3,4,7,9,12,14,16,19,23,25,28,30,31,33,34,36,38],useful:[12,34],user:[0,34,36],uses:[14,33,34,35,37],using:[9,14,16,20,24,32,33,34,35,36,37,38],usual:[9,33,35],util:37,valid:33,valu:[5,8,35,36],variant:35,variou:[5,7,36],veri:34,version:[0,26,34,36,38],vgroup:35,via:[9,14,33,34,36],view:[33,34,35,38],wai:[8,20,24,32,33,34,35,36,37],wait:[1,5,7,8,26,35,36,37],want:[33,34,36,37],warn:[9,14,16],warranti:[33,34,35,37,38],well:[33,36],whatev:[8,33,34],when:[3,5,8,9,12,14,16,20,24,28,30,32,34,36,38],whenev:[3,4,11,14,20,24,32,33,34],where:[4,9,14,16,36],whether:[2,3,4,12,18,22,28,30,33,38],which:[7,9,14,16,20,24,26,32,33,34,36,38],whose:[18,22,30,36],width:35,window:30,wish:9,without:[5,7,8,33,34,35,36,37,38],won:[36,37],work:[34,35,38],worker:[4,10,13,14,15,16,26,35,38],worker_pool:[10,13,15,26,36],would:34,wrap:28,wrapper:[0,2,25,38],write:33,www:[33,34,35,37,38],wxpython:[32,37],yet:36,yield:[3,34],you:[1,33,34,35,36,37],your:[34,35,36,38],zero:[11,20,24,28,32,33]},titles:["traits_futures package","traits_futures.api module","traits_futures.background_call module","traits_futures.background_iteration module","traits_futures.background_progress module","traits_futures.base_future module","traits_futures.exception_handling module","traits_futures.future_states module","traits_futures.i_future module","traits_futures.i_message_router module","traits_futures.i_parallel_context module","traits_futures.i_pingee module","traits_futures.i_task_specification module","traits_futures.multiprocessing_context module","traits_futures.multiprocessing_router module","traits_futures.multithreading_context module","traits_futures.multithreading_router module","traits_futures.null package","traits_futures.null.gui_test_assistant module","traits_futures.null.init module","traits_futures.null.pinger module","traits_futures.qt package","traits_futures.qt.gui_test_assistant module","traits_futures.qt.init module","traits_futures.qt.pinger module","traits_futures.toolkit_support module","traits_futures.traits_executor module","traits_futures.version module","traits_futures.wrappers module","traits_futures.wx package","traits_futures.wx.gui_test_assistant module","traits_futures.wx.init module","traits_futures.wx.pinger module","Advanced topics","Making tasks interruptible","Contexts and multiprocessing","Introduction","Testing Traits Futures code","Traits Futures: reactive background processing for Traits and TraitsUI"],titleterms:{"\u03c0":34,"function":1,"new":33,"null":[17,18,19,20],The:33,Using:36,advanc:33,all:33,api:[1,9,38],approxim:34,background:[1,33,36,38],background_cal:2,background_iter:3,background_progress:4,base_futur:5,buzz:33,callabl:33,cancel:[34,36],code:37,context:[1,35],creat:33,defin:1,document:38,exampl:[33,34,37],exception_handl:6,executor:[1,36],featur:38,fizz:33,foreground:33,futur:[1,33,36,37,38],future_st:7,get:36,gui:33,gui_test_assist:[18,22,30],guid:38,i_futur:8,i_message_rout:9,i_parallel_context:10,i_pinge:11,i_task_specif:12,implement:14,indic:38,init:[19,23,31],interrupt:34,introduct:36,limit:38,make:34,messag:33,modul:[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,18,19,20,22,23,24,25,26,27,28,30,31,32],multiprocess:35,multiprocessing_context:13,multiprocessing_rout:14,multithreading_context:15,multithreading_rout:16,object:36,overview:[9,14],own:33,packag:[0,17,21,29],parallel:1,partial:34,pinger:[20,24,32],pool:36,process:38,put:33,quick:38,reactiv:38,result:[34,36],send:34,share:36,specif:33,start:38,state:[1,36],stop:36,submiss:1,submit:[33,36],support:1,tabl:38,task:[1,33,34,36],test:37,togeth:33,toolkit_support:25,topic:33,trait:[37,38],traits_executor:26,traits_futur:[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32],traitsui:38,type:[1,33],user:[1,38],version:27,work:[33,36],worker:36,wrapper:28,your:33}})