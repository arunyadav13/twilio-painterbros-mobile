import React from "react";
import { Button, Image,Text } from "react-native";
import {
  getStatusOfCallOnMyNumber,
  countTheCallsActive
} from "../assets/library/helper";
import smallplayicon from "../assets/images/smallpauseiconactive.svg";
import smallpauseicon from "../../CallListContainer/assets/images/holdicon.svg";
import { resumeCall, holdCall } from "../assets/library/api";
const { REACT_APP_STATIC_ASSETS_BASE_URL } = process.env;

class HoldResumeButton extends React.Component {
  constructor(props) {
    super(props);
  }

  prepareTOHoldOrResumeTheCall = async () => {
    const { alterButtonDiableProperty } = this.props;
    alterButtonDiableProperty(true);
    const {
      callElement,
      user,
      callDetails,
      alterDisplayIndividualCallDetails,
      deviceId
    } = this.props;

    if (callElement.conference.status === "hold") {
      const resumeCallResponse = await resumeCall(
        callElement.conference.sid,
        user.identity,
        callElement.call.sid,
        getStatusOfCallOnMyNumber(callElement, user).callSid,
        user.number,
        user.tenant_id,
        user.subtenant_id,
        callDetails,
        deviceId
      );
      if (resumeCallResponse.data.data.message === "success") {
        alterButtonDiableProperty(false);
        alterDisplayIndividualCallDetails(true);
      }
    } else {
      const holdCallResponse = await holdCall(
        callElement.conference.sid,
        user.identity,
        getStatusOfCallOnMyNumber(callElement, user).callSid,
        user.tenant_id,
        user.subtenant_id
      );
      if (holdCallResponse) {
        const countOfCallsOnHold = await countTheCallsActive(callDetails);
        if (countOfCallsOnHold === 0) {
          alterButtonDiableProperty(false);
          alterDisplayIndividualCallDetails(false);
        }
      }
    }
  };

  render() {
    const { callElement, disabled, deviceId } = this.props;
    return (
      <Button
        className="removecolorbut pauseplayicon"
        onPress={() => this.prepareTOHoldOrResumeTheCall()}
        disabled={disabled}
      >
        <Image
          className="holdresumesmallicon"
          source={`${REACT_APP_STATIC_ASSETS_BASE_URL}${
            callElement.conference.status === "hold"
              ? smallplayicon
              : smallpauseicon
          }`}
        />
        <Text className="holdResumeText">
          {callElement.conference.status === "hold" ? "Resume" : "Hold"}
        </Text>
      </Button>
    );
  }
}

export default HoldResumeButton;
