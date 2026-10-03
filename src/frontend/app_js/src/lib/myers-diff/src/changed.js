function changed(change) {
	if (!change.del && change.add) {
		return true;
	}
	if (change.del && !change.add) {
		return true;
	}
	return false;
}

export default changed;
