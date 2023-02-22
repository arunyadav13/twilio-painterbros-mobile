import React from "react";
import AcceptCallButton from "./AcceptCallButton";
import EndConferenceButton from "./EndConferenceButton";
import outgoingcallicon from "../../../Dialer/CallListContainer/assets/images/phoneoutgoing.svg";
import inboundicon from "../../../Dialer/CallListContainer/assets/images/inbound.svg";
import {
  displayCallerName,
  displayCallerNumber,
  getWarmTransferParticipant
} from "../assets/library/helper";
import HoldResumeButton from "./HoldResumeButton";
const { REACT_APP_STATIC_ASSETS_BASE_URL } = process.env;

class IndividualCallItem extends React.Component {
  constructor(props) {
    super(props);
  }

  render() {
    const {
      callElement,
      conn,
      prepareToReceiveIncomingCall,
      user,
      callDetails,
      alterDisplayIndividualCallDetails,
      rejectCall,
      activeCallCount,
      alterButtonDiableProperty,
      shouldDisableButton,
      deviceId
    } = this.props;
    return (
      <div>
        <div
          className={`callListContainer secondaryParticipant outgoingcall ${
            activeCallCount > 0 && `${callElement.call.direction} `
          } ${callElement.conference.status}`}
        >
          {
            <div className="phonebookbox">
              <div className="firsttext">
                <div className="Nameletters">
                  <span>
                    <img
                      alt=""
                      src={`${REACT_APP_STATIC_ASSETS_BASE_URL}${
                        callElement.call.direction === "inbound"
                          ? inboundicon
                          : outgoingcallicon
                      }`}
                    />
                  </span>
                </div>
              </div>
              <div className="phonebooknum">
                <span
                  data-bs-toggle="tooltip"
                  data-bs-placement="bottom"
                  title={displayCallerName(callElement)}
                >
                  {displayCallerName(callElement)}
                </span>
                <span>{displayCallerNumber(callElement)}</span>
                <span>
                  {callElement.conference.status}{" "}
                  {callElement.conference.participants.length > 2 &&
                    ` | Conference call with ${callElement.conference.participants.length} participants`}
                </span>
              </div>
              <div className="phonebookicon">
                {(callElement.conference.status === "hold" ||
                  callElement.conference.status === "in-progress") && (
                  <HoldResumeButton
                    callElement={callElement}
                    user={user}
                    callDetails={callDetails}
                    alterDisplayIndividualCallDetails={
                      alterDisplayIndividualCallDetails
                    }
                    alterButtonDiableProperty={alterButtonDiableProperty}
                    disabled={shouldDisableButton}
                    deviceId={deviceId}
                  />
                )}
                {callElement.conference.status !== "in-progress" &&
                  callElement.conference.status !== "hold" &&
                  callElement.call.direction === "inbound" && (
                    <AcceptCallButton
                      prepareToReceiveIncomingCall={
                        prepareToReceiveIncomingCall
                      }
                      caller={displayCallerNumber(callElement)}
                      shouldDisableButton={shouldDisableButton}
                      alterButtonDiableProperty={alterButtonDiableProperty}
                    />
                  )}

                {getWarmTransferParticipant(callElement).length <= 0 && (
                  <EndConferenceButton
                    callElement={callElement}
                    currentConnection={conn}
                    user={user}
                    rejectCall={rejectCall}
                    conferenaceSid={callElement.conference.sid}
                    shouldDisableButton={shouldDisableButton}
                    alterButtonDiableProperty={alterButtonDiableProperty}
                  />
                )}
              </div>
            </div>
          }
        </div>
      </div>
    );
  }
}

export default IndividualCallItem;
