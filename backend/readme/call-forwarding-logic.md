

# Call Forwarding Logic

* worker1 receive the call
    * worker1 call event, call_status=completed 
        * push call log to worker1 sync list
            * "forwarding": null

* worker 1 no answer, worker2 receive the call
    * worker1 call event, call_status=no-answer 
        * push call log to wokrer1 sync list
            * "forwarding": {"from": null, "to": "worker 2 details", "answeredBy": null}
    
    * worker2 call event, call_status=in-progress 
        * Update call forwarding details for worker 1
             * "forwarding": { "answeredBy": "woker 2 details"}

    * worker2 call event, call_status=completed
        * push call log to wokrer2 sync list
            * "forwarding": { "from": "worker 1 details", "to": null, "answeredBy": null}

* worker 1 no answer, worker 2 no answer, worker 3 receive the call 
    * worker1 call event, call_status=no-answer 
        * push call log to wokrer1 sync list
            * "forwarding": {"from": null, "to": "worker 2 details", "answeredBy": null}

    * worker2 call event, call_status=no-answer 
        * push call log to wokrer2 sync list
            * "forwarding": {"from": "worker 1 details", "to": "worker 3 details", "answeredBy": null}
    
    * worker3 call event, call_status=in-progress 
        * Update call forwarding details for worker 1
            *  "forwarding": { "answeredBy": "woker 3 details"}
        * Update call forwarding details for worker 2
            * "forwarding": { "answeredBy": "woker 3 details"}

    * worker3 call event, call_status=completed
        * push call log to wokrer3 sync list
            * "forwarding": { "from": "worker 2 details", "to": null, "answeredBy": null}

* worker 1 no answer, worker 2 no answer, worker 3 no answer, send to voicemail
   *  worker1 call event, call_status=no-answer 
        * push call log to wokrer1 sync list
            * "forwarding": {"from": null, "to": "worker 2 details", "answeredBy": null}
            
    * worker2 call event, call_status=no-answer 
        * push call log to wokrer2 sync list
            * "forwarding": {"from": "worker 1 details", "to": "worker 3 details", "answeredBy": null}
            
    * worker3 call event, call_status=no-answer 
        * push call log to wokrer3 sync list
            * "forwarding": {"from": "worker 2 details", "to": null, "answeredBy": null}

    * on voicemail complete event 
        * push call log to worker 1 sync list
            * "forwarding": {"voicemail": "voicemail worker details"}
        * push call log to worker 2 sync list
            * "forwarding": {"voicemail": "voicemail worker details"}
        * push call log to worker 3 sync list
            * "forwarding": {"voicemail": "voicemail worker details"}
        
        

