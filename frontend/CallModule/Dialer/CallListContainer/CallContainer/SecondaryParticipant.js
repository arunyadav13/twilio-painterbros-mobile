import React from "react";
import EndConferenceButton from "./EndConferenceButton";
import outgoingcallicon from "../assets/images/phoneoutgoing.svg";
import { getWarmTransferParticipant } from "../assets/library/helper";
const { REACT_APP_STATIC_ASSETS_BASE_URL } = process.env;

class SecondaryParticipant extends React.Component {
  constructor(props) {
    super(props);
  }

  render() {
    const {
      callElement,
      participantElement,
      conn,
      user,
      alterButtonDiableProperty,
      shouldDisableButton
    } = this.props;
    return (
      <div className="secondaryParticipant conferencecall">
        <div className="conferencecalllist">
          <div className="phonebookbox">
            <div className="firsttext">
              <div className="Nameletters">
                <span>
                  <img alt="" src={`${REACT_APP_STATIC_ASSETS_BASE_URL}${outgoingcallicon}`} />
                </span>
              </div>
            </div>
            <div className="phonebooknum">
              <span
                data-bs-toggle="tooltip"
                data-bs-placement="bottom"
                title={participantElement.name}
              >
                {participantElement.name}
              </span>
              <span>{participantElement.to}</span>
              <span>{participantElement.callStatus}</span>
            </div>

            {callElement.conference.sid !== "" &&
              getWarmTransferParticipant(callElement).length <= 0 && (
                <div className="phonebookicon">
                  <EndConferenceButton
                    callElement={participantElement}
                    currentConnection={conn}
                    user={user}
                    conferenaceSid={callElement.conference.sid}
                    alterButtonDiableProperty={alterButtonDiableProperty}
                    shouldDisableButton={shouldDisableButton}
                  />
                </div>
              )}
          </div>
        </div>
      </div>
    );
  }
}

export default SecondaryParticipant;
