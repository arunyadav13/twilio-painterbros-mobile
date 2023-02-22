import React from "react";
import { Button, Image, Text } from "react-native";
import muteicon from "../assets/images/muteiconactive.svg";
import speaker from "../assets/images/unmuteiconactive.svg";
const { REACT_APP_STATIC_ASSETS_BASE_URL } = process.env;

class MuteParticipant extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      isMuted: false
    };
  }

  toggleMute = () => {
    const { isMuted } = this.state;
    const { currentConnection } = this.props;
    currentConnection.mute(!isMuted);
    this.setState({ ...this.state, isMuted: !isMuted });
  };

  render() {
    const { isMuted } = this.state;
    const { disabled } = this.props;
    return (
      <Button
        className={`removecolorbut muteicon ${
          isMuted ? "speakerOff" : "speakerOn"
        }`}
        onPress={() => this.toggleMute()}
        disabled={disabled}
      >
        {!isMuted ? <Image source={`${REACT_APP_STATIC_ASSETS_BASE_URL}${muteicon}`} /> : <Image source={`${REACT_APP_STATIC_ASSETS_BASE_URL}${speaker}`} />}
        <Text>{!isMuted ? "Mute" : "Unmute"}</Text>
      </Button>
    );
  }
}
export default MuteParticipant;
