import React from "react";
import { Button, Image } from "react-native";
import { endConference } from "../assets/library/api";
import endcallicon from "../assets/images/endcall.svg";
import { getParticipantToPutOnHold } from "../assets/library/helper";
import { removeConferenceParticipant } from "../assets/library/api";
const { REACT_APP_STATIC_ASSETS_BASE_URL } = process.env;

class EndConferenceButton extends React.Component {
  constructor(props) {
    super(props);
  }

  prepareToEndOrLeaveConference = async () => {
    const {
      callElement,
      user,
      currentConnection,
      rejectCall,
      conferenaceSid,
    } = this.props;

    let isSourceOrDestination = callElement;
    if (callElement.call) {
      isSourceOrDestination = getParticipantToPutOnHold(callElement);
    }

    if (
      isSourceOrDestination.type === "source" ||
      isSourceOrDestination.type === "destination"
    ) {
      if (callElement.conference.status === "hold") {
        await endConference(
          callElement.conference.sid,
          user.tenant_id,
          user.subtenant_id
        );
      } else if (
        callElement.call.direction === "inbound" &&
        (callElement.conference.status === "initiated" ||
          callElement.conference.status === "ringing")
      ) {
        rejectCall(isSourceOrDestination.from_);
      } else {
        currentConnection.disconnect();
      }
    } else {
      await removeConferenceParticipant(
        user.tenant_id,
        user.subtenant_id,
        conferenaceSid,
        isSourceOrDestination.callSid
      );
    }
  };

  render() {
    const { shouldDisableButton, alterButtonDiableProperty } = this.props;
    return (
      <Button
        className="removecolorbut endcallicon"
        onPress={() => {
          alterButtonDiableProperty(true);
          this.prepareToEndOrLeaveConference();
        }}
        disabled={shouldDisableButton}
      >
        <Image source={`${REACT_APP_STATIC_ASSETS_BASE_URL}${endcallicon}`} />
      </Button>
    );
  }
}

export default EndConferenceButton;
