import React from "react";
import { Button } from "react-bootstrap";
import endcallicon from "../assets/images/endcall.svg";
const { REACT_APP_STATIC_ASSETS_BASE_URL } = process.env;

class EndCallButton extends React.Component {
  constructor(props) {
    super(props);
  }

  endCall = () => {
    const { conferenceSid, removeParticipant, participantElement, conn, user } =
      this.props;
    if (
      participantElement.type !== "" &&
      participantElement.callStatus === "in-progress"
    ) {
      conn.disconnect();
    } else {
      removeParticipant(user.tenant_id, user.subtenant_id, conferenceSid, participantElement.callSid);
    }
  };

  render() {
    return (
      <Button
        className="removecolorbut smallndcallicon"
        onClick={() => this.endCall()}
      >
        <img alt="" src={`${REACT_APP_STATIC_ASSETS_BASE_URL}${endcallicon}`} />
      </Button>
    );
  }
}

export default EndCallButton;
